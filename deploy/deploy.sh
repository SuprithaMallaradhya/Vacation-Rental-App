#!/usr/bin/env bash
# Azure deployment for the Vacation Rental App.
#
#   Internet ─▶ Standard Load Balancer (public IP + DNS name, health probe /ready)
#                 └▶ VM Scale Set (Ubuntu, CPU autoscale min..max)
#                      each VM: docker compose → nginx (React + /api proxy) + FastAPI
#                 ─▶ Azure Database for PostgreSQL Flexible Server (B1ms)
#                 ─▶ Azure Blob Storage (Host photo/video uploads)
#
# Usage: ./deploy/deploy.sh <command>      (run from the repository root; see docs/deployment.md)
#   init         create deploy/azure.env with unique names and generated secrets
#   check        verify az login, subscription, region and VM size availability
#   infra        resource group, network, load balancer, PostgreSQL, Blob Storage (run once)
#   db-load      copy your local seeded database into Azure PostgreSQL (run once, needs Docker)
#   db-migrate   apply new Alembic migrations to Azure PostgreSQL (after schema changes)
#   vms          create the scale set + autoscale rules (run after infra and db-load)
#   status       URL, instances, health
#   update       pull the newest images on every running VM and restart containers
#   logs         last container log lines from every VM
#   reconfigure  rebuild the scale set with re-rendered settings (after editing azure.env)
#   pause        scale to 0 and stop PostgreSQL (saves credit while nobody is testing)
#   resume       start PostgreSQL and scale back to MIN_INSTANCES with autoscale on
#   destroy      delete EVERYTHING (the whole resource group)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEPLOY="$ROOT/deploy"
CONFIG="$DEPLOY/azure.env"
OUT="$DEPLOY/out"
PY="$(command -v python3 || command -v python3.12 || true)"
[ -n "$PY" ] || { echo "python3 is required" >&2; exit 1; }

say()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!!  %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[1;31mxx  %s\033[0m\n' "$*" >&2; exit 1; }

secret() { "$PY" -c "import secrets,string;a=string.ascii_letters+string.digits;print(''.join(secrets.choice(a) for _ in range($1)))"; }

load_config() {
  [ -f "$CONFIG" ] || die "Missing deploy/azure.env. Run: ./deploy/deploy.sh init"
  set -a
  # shellcheck disable=SC1090
  . "$CONFIG"
  set +a
  [ -n "${SUFFIX:-}" ] && [ -n "${DB_PASSWORD:-}" ] && [ -n "${JWT_SECRET_KEY:-}" ] \
    || die "SUFFIX, DB_PASSWORD and JWT_SECRET_KEY must be set in deploy/azure.env (run init)"
  DB_SERVER="vr-db-$SUFFIX"
  STORAGE="vrmedia$SUFFIX"
  CONTAINER="listing-media"
  DNS_LABEL="vr-demo-$SUFFIX"
  DB_HOST="$DB_SERVER.postgres.database.azure.com"
  APP_URL="http://$DNS_LABEL.$LOCATION.cloudapp.azure.com"
  command -v az >/dev/null || die "Azure CLI not found. macOS: brew install azure-cli"
}

lb_ip() { az network public-ip show -g "$RESOURCE_GROUP" -n "$PUBLIC_IP" --query ipAddress -o tsv; }
my_ip() { curl -fsS https://api.ipify.org; }
storage_key() { az storage account keys list -g "$RESOURCE_GROUP" -n "$STORAGE" --query '[0].value' -o tsv; }
exists() { "$@" >/dev/null 2>&1; }

cmd_init() {
  [ -f "$CONFIG" ] && die "deploy/azure.env already exists; edit it instead"
  local suffix; suffix="$("$PY" -c "import secrets,string;print(''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(6)))")"
  sed -e "s/^SUFFIX=.*/SUFFIX=$suffix/" \
      -e "s/^DB_PASSWORD=.*/DB_PASSWORD=$(secret 28)/" \
      -e "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$(secret 64)/" \
      "$DEPLOY/azure.env.example" > "$CONFIG"
  chmod 600 "$CONFIG"
  say "Created deploy/azure.env (suffix $suffix). It holds secrets and is ignored by Git."
  echo "Your app will be at: http://vr-demo-$suffix.<LOCATION>.cloudapp.azure.com"
}

cmd_check() {
  load_config
  say "Azure account"
  az account show --query '{subscription:name, id:id, user:user.name}' -o table \
    || die "Not logged in. Run: az login"
  say "Registering resource providers (first time only, safe to repeat)"
  for p in Microsoft.Compute Microsoft.Network Microsoft.DBforPostgreSQL Microsoft.Storage Microsoft.Insights; do
    az provider register --namespace "$p" >/dev/null
  done
  say "Is $VM_SIZE available in $LOCATION for this subscription?"
  local r
  r="$(az vm list-skus -l "$LOCATION" --size "$VM_SIZE" --resource-type virtualMachines \
        --query '[0].{name:name, restricted:length(restrictions)}' -o tsv)"
  [ -n "$r" ] || die "$VM_SIZE is not offered in $LOCATION. Try another LOCATION in deploy/azure.env"
  case "$r" in *$'\t'0) echo "OK: $r" ;; *) die "$VM_SIZE is restricted in $LOCATION ($r). Try another region";; esac
  say "Check passed. Next: ./deploy/deploy.sh infra"
}

cmd_infra() {
  load_config
  say "Resource group $RESOURCE_GROUP in $LOCATION"
  az group create -n "$RESOURCE_GROUP" -l "$LOCATION" -o none

  say "Network: NSG (allow HTTP 80), VNet, subnet"
  az network nsg create -g "$RESOURCE_GROUP" -n "$NSG" -o none
  exists az network nsg rule show -g "$RESOURCE_GROUP" --nsg-name "$NSG" -n allow-http || \
    az network nsg rule create -g "$RESOURCE_GROUP" --nsg-name "$NSG" -n allow-http --priority 100 \
      --direction Inbound --access Allow --protocol Tcp --source-address-prefixes Internet \
      --destination-port-ranges 80 -o none
  exists az network vnet show -g "$RESOURCE_GROUP" -n "$VNET" || \
    az network vnet create -g "$RESOURCE_GROUP" -n "$VNET" --address-prefixes 10.10.0.0/16 \
    --subnet-name "$SUBNET" --subnet-prefixes 10.10.1.0/24 --network-security-group "$NSG" -o none

  say "Public IP with DNS name $DNS_LABEL"
  exists az network public-ip show -g "$RESOURCE_GROUP" -n "$PUBLIC_IP" || \
    az network public-ip create -g "$RESOURCE_GROUP" -n "$PUBLIC_IP" --sku Standard \
    --allocation-method Static --dns-name "$DNS_LABEL" -o none

  say "Standard Load Balancer: frontend, backend pool, /ready probe, HTTP rule, outbound rule"
  exists az network lb show -g "$RESOURCE_GROUP" -n "$LB" || \
    az network lb create -g "$RESOURCE_GROUP" -n "$LB" --sku Standard --public-ip-address "$PUBLIC_IP" \
      --frontend-ip-name fe --backend-pool-name pool -o none
  exists az network lb probe show -g "$RESOURCE_GROUP" --lb-name "$LB" -n ready || \
    az network lb probe create -g "$RESOURCE_GROUP" --lb-name "$LB" -n ready --protocol Http \
      --port 80 --path /ready --interval 15 -o none
  exists az network lb rule show -g "$RESOURCE_GROUP" --lb-name "$LB" -n http || \
    az network lb rule create -g "$RESOURCE_GROUP" --lb-name "$LB" -n http --protocol Tcp \
      --frontend-port 80 --backend-port 80 --frontend-ip-name fe --backend-pool-name pool \
      --probe-name ready --disable-outbound-snat true --idle-timeout 4 -o none
  # VMs in a new VNet have no internet access by default; this gives them outbound
  # (apt, image pulls, PostgreSQL) through the load balancer's public IP.
  exists az network lb outbound-rule show -g "$RESOURCE_GROUP" --lb-name "$LB" -n outbound || \
    az network lb outbound-rule create -g "$RESOURCE_GROUP" --lb-name "$LB" -n outbound \
      --frontend-ip-configs fe --protocol All --address-pool pool -o none

  local ip; ip="$(lb_ip)"

  say "PostgreSQL Flexible Server $DB_SERVER (Burstable B1ms, 32 GB) — takes 5–10 minutes"
  exists az postgres flexible-server show -g "$RESOURCE_GROUP" -n "$DB_SERVER" || \
    az postgres flexible-server create -g "$RESOURCE_GROUP" -n "$DB_SERVER" -l "$LOCATION" \
      --tier Burstable --sku-name Standard_B1ms --storage-size 32 --version 16 \
      --admin-user "$DB_ADMIN" --admin-password "$DB_PASSWORD" \
      --public-access None --backup-retention 7 --yes -o none
  # Newer CLIs create the server with public access disabled; enable it (the firewall still blocks every IP not listed).
  az postgres flexible-server update -g "$RESOURCE_GROUP" -n "$DB_SERVER" --public-access Enabled -o none
  # The first migration runs CREATE EXTENSION btree_gist; Azure only allows listed extensions.
  az postgres flexible-server parameter set -g "$RESOURCE_GROUP" --server-name "$DB_SERVER" \
    --name azure.extensions --value BTREE_GIST -o none
  exists az postgres flexible-server db show -g "$RESOURCE_GROUP" --server-name "$DB_SERVER" --name "$DB_NAME" || \
    az postgres flexible-server db create -g "$RESOURCE_GROUP" --server-name "$DB_SERVER" \
      --name "$DB_NAME" -o none
  # Only the VMs (outbound via the LB IP) may connect. db-load adds your own IP temporarily.
  az postgres flexible-server firewall-rule create -g "$RESOURCE_GROUP" --server-name "$DB_SERVER" \
    --name lb-outbound --start-ip-address "$ip" --end-ip-address "$ip" -o none

  say "Blob Storage $STORAGE with public-read container '$CONTAINER' and browser-upload CORS"
  exists az storage account show -g "$RESOURCE_GROUP" -n "$STORAGE" || \
    az storage account create -g "$RESOURCE_GROUP" -n "$STORAGE" -l "$LOCATION" --sku Standard_LRS \
      --kind StorageV2 --min-tls-version TLS1_2 --allow-blob-public-access true -o none
  local key; key="$(storage_key)"
  az storage container create --name "$CONTAINER" --account-name "$STORAGE" --account-key "$key" \
    --public-access blob -o none
  az storage cors clear --services b --account-name "$STORAGE" --account-key "$key"
  az storage cors add --services b --methods GET HEAD PUT OPTIONS --origins "$APP_URL" \
    --allowed-headers '*' --exposed-headers '*' --max-age 3600 \
    --account-name "$STORAGE" --account-key "$key"

  say "Infrastructure ready. Load balancer IP: $ip"
  echo "Next: ./deploy/deploy.sh db-load   (then: ./deploy/deploy.sh vms)"
}

render_cloud_init() {
  mkdir -p "$OUT"; chmod 700 "$OUT"
  local key; key="$(storage_key)"
  cat > "$OUT/.env.prod" <<EOF
APP_ENV=production
APP_NAME=Vacation Rental API
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://$DB_ADMIN:$DB_PASSWORD@$DB_HOST:5432/$DB_NAME?ssl=require
CORS_ORIGINS=$APP_URL
API_PUBLIC_BASE_URL=$APP_URL
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_EXPIRE_MINUTES=60
LOGIN_MAX_ATTEMPTS=10
LOGIN_WINDOW_SECONDS=60
STORAGE_PROVIDER=azure
AZURE_STORAGE_ACCOUNT_NAME=$STORAGE
AZURE_STORAGE_ACCOUNT_KEY=$key
AZURE_STORAGE_CONTAINER=$CONTAINER
EOF
  chmod 600 "$OUT/.env.prod"
  sed -e "s#\${API_IMAGE:-[^}]*}#$API_IMAGE#" -e "s#\${WEB_IMAGE:-[^}]*}#$WEB_IMAGE#" \
    "$DEPLOY/compose.prod.yaml" > "$OUT/compose.yaml"
  COMPOSE_B64="$(base64 < "$OUT/compose.yaml" | tr -d '\n')" \
  ENV_B64="$(base64 < "$OUT/.env.prod" | tr -d '\n')" \
  GHCR_USER="${GHCR_USER:-}" GHCR_TOKEN="${GHCR_TOKEN:-}" \
  "$PY" - "$DEPLOY/cloud-init.yaml" "$OUT/cloud-init.yaml" <<'PY'
import os, string, sys
text = open(sys.argv[1]).read()
open(sys.argv[2], "w").write(string.Template(text).substitute(os.environ))
PY
  chmod 600 "$OUT/cloud-init.yaml"
}

cmd_vms() {
  load_config
  exists az vmss show -g "$RESOURCE_GROUP" -n "$VMSS" && die "$VMSS already exists. Use: update, or reconfigure"
  say "Rendering cloud-init (secrets stay in deploy/out/, ignored by Git)"
  render_cloud_init
  say "VM Scale Set $VMSS ($VM_SIZE, $MIN_INSTANCES instance(s)) behind $LB"
  az vmss create -g "$RESOURCE_GROUP" -n "$VMSS" --orchestration-mode Uniform \
    --image Canonical:ubuntu-24_04-lts:server:latest --vm-sku "$VM_SIZE" \
    --instance-count "$MIN_INSTANCES" --upgrade-policy-mode Automatic \
    --vnet-name "$VNET" --subnet "$SUBNET" --lb "$LB" --backend-pool-name pool \
    --storage-sku Premium_LRS --os-disk-size-gb 64 \
    --admin-username azureuser --generate-ssh-keys \
    --custom-data "$OUT/cloud-init.yaml" -o none
  say "Autoscale: $MIN_INSTANCES..$MAX_INSTANCES instances on average CPU"
  az monitor autoscale create -g "$RESOURCE_GROUP" --resource "$VMSS" \
    --resource-type Microsoft.Compute/virtualMachineScaleSets --name "$AUTOSCALE" \
    --min-count "$MIN_INSTANCES" --max-count "$MAX_INSTANCES" --count "$MIN_INSTANCES" -o none
  az monitor autoscale rule create -g "$RESOURCE_GROUP" --autoscale-name "$AUTOSCALE" \
    --condition "Percentage CPU > $SCALE_OUT_CPU avg 5m" --scale out 1 --cooldown 5 -o none
  az monitor autoscale rule create -g "$RESOURCE_GROUP" --autoscale-name "$AUTOSCALE" \
    --condition "Percentage CPU < $SCALE_IN_CPU avg 10m" --scale in 1 --cooldown 5 -o none
  say "Done. First boot installs Docker and pulls images (~3–5 min). Then: ./deploy/deploy.sh status"
  echo "App URL: $APP_URL"
}

cmd_status() {
  load_config
  say "App URL: $APP_URL   (LB IP $(lb_ip))"
  az vmss list-instances -g "$RESOURCE_GROUP" -n "$VMSS" \
    --query '[].{id:instanceId, name:name, state:provisioningState}' -o table 2>/dev/null || warn "No scale set yet"
  az monitor autoscale show -g "$RESOURCE_GROUP" -n "$AUTOSCALE" \
    --query '{enabled:enabled, min:profiles[0].capacity.minimum, max:profiles[0].capacity.maximum}' -o table 2>/dev/null || true
  say "Health through the load balancer"
  curl -s -m 10 -o /dev/null -w "/health %{http_code}\n" "$APP_URL/health" || true
  curl -s -m 10 -w "\n" "$APP_URL/ready" || warn "/ready not reachable yet"
}

run_on_all() {
  local ids; ids="$(az vmss list-instances -g "$RESOURCE_GROUP" -n "$VMSS" --query '[].instanceId' -o tsv)"
  [ -n "$ids" ] || die "No running instances"
  for id in $ids; do
    say "Instance $id"
    az vmss run-command invoke -g "$RESOURCE_GROUP" -n "$VMSS" --instance-id "$id" \
      --command-id RunShellScript --scripts "$1" --query 'value[0].message' -o tsv
  done
}

cmd_update() { load_config; run_on_all "/opt/vacation-rental/start.sh && docker image prune -f"; }
cmd_logs()   { load_config; run_on_all "cd /opt/vacation-rental && docker compose ps && docker compose logs --tail 40"; }

cmd_reconfigure() {
  load_config
  say "Deleting scale set $VMSS (load balancer, database and storage are kept)"
  az monitor autoscale delete -g "$RESOURCE_GROUP" -n "$AUTOSCALE" 2>/dev/null || true
  az vmss delete -g "$RESOURCE_GROUP" -n "$VMSS" 2>/dev/null || true
  cmd_vms
}

with_temporary_firewall() {   # $1 = function to run while your IP may reach PostgreSQL
  local ip; ip="$(my_ip)"
  say "Allowing your IP $ip on PostgreSQL temporarily"
  az postgres flexible-server firewall-rule create -g "$RESOURCE_GROUP" --server-name "$DB_SERVER" \
    --name laptop --start-ip-address "$ip" --end-ip-address "$ip" -o none
  local rc=0; "$1" || rc=$?
  az postgres flexible-server firewall-rule delete -g "$RESOURCE_GROUP" --server-name "$DB_SERVER" \
    --name laptop --yes -o none || warn "Remove the 'laptop' firewall rule manually"
  return $rc
}

PSQL_IMAGE=postgres:16-alpine
azure_psql() { docker run --rm -i -e PGPASSWORD="$DB_PASSWORD" "$PSQL_IMAGE" \
  psql "host=$DB_HOST port=5432 dbname=$DB_NAME user=$DB_ADMIN sslmode=require" -v ON_ERROR_STOP=1 "$@"; }

_db_load() {
  if [ "$(azure_psql -tAc "select to_regclass('public.listings') is not null")" = "t" ]; then
    die "Azure database already has tables; refusing to load over it"
  fi
  say "Copying local vacation_rental_dev → Azure $DB_NAME"
  (cd "$ROOT" && docker compose exec -T postgres-dev \
      pg_dump -U vacation -d vacation_rental_dev --no-owner --no-privileges --no-comments) \
    | azure_psql -q
  say "Loaded:"; azure_psql -c "select (select count(*) from users) users, (select count(*) from listings) listings, (select count(*) from bookings) bookings, (select version_num from alembic_version) schema"
}

cmd_db_load() {
  load_config
  command -v docker >/dev/null || die "Docker is required (Docker Desktop running)"
  (cd "$ROOT" && docker compose ps --status running postgres-dev | grep -q postgres-dev) \
    || die "Local dev database not running. Run: make db-up && make migrate && make seed"
  with_temporary_firewall _db_load
}

_db_migrate() {
  (cd "$ROOT/backend" && APP_ENV=production JWT_SECRET_KEY="$JWT_SECRET_KEY" \
    DATABASE_URL="postgresql+asyncpg://$DB_ADMIN:$DB_PASSWORD@$DB_HOST:5432/$DB_NAME?ssl=require" \
    ./.venv/bin/python -m alembic upgrade head)
}
cmd_db_migrate() { load_config; [ -x "$ROOT/backend/.venv/bin/python" ] || die "Run make setup first"; with_temporary_firewall _db_migrate; }

cmd_pause() {
  load_config
  say "Pausing: autoscale off, 0 instances, PostgreSQL stopped (public IP still costs a little)"
  az monitor autoscale update -g "$RESOURCE_GROUP" -n "$AUTOSCALE" --enabled false -o none || true
  az vmss scale -g "$RESOURCE_GROUP" -n "$VMSS" --new-capacity 0 -o none || true
  az postgres flexible-server stop -g "$RESOURCE_GROUP" -n "$DB_SERVER" -o none || true
  warn "Azure restarts a stopped PostgreSQL server automatically after 7 days."
}

cmd_resume() {
  load_config
  say "Resuming: PostgreSQL start, $MIN_INSTANCES instance(s), autoscale on"
  az postgres flexible-server start -g "$RESOURCE_GROUP" -n "$DB_SERVER" -o none || true
  az vmss scale -g "$RESOURCE_GROUP" -n "$VMSS" --new-capacity "$MIN_INSTANCES" -o none
  az monitor autoscale update -g "$RESOURCE_GROUP" -n "$AUTOSCALE" --enabled true -o none
  echo "Give it ~3 minutes, then: ./deploy/deploy.sh status"
}

cmd_destroy() {
  load_config
  warn "This deletes resource group $RESOURCE_GROUP: VMs, load balancer, database (all data) and storage."
  printf 'Type the resource group name to confirm: '; read -r answer
  [ "$answer" = "$RESOURCE_GROUP" ] || die "Not confirmed"
  az group delete -n "$RESOURCE_GROUP" --yes --no-wait
  say "Deletion started (takes a few minutes)."
}

case "${1:-}" in
  init) cmd_init ;; check) cmd_check ;; infra) cmd_infra ;; vms) cmd_vms ;;
  status) cmd_status ;; update) cmd_update ;; logs) cmd_logs ;; reconfigure) cmd_reconfigure ;;
  db-load) cmd_db_load ;; db-migrate) cmd_db_migrate ;;
  pause) cmd_pause ;; resume) cmd_resume ;; destroy) cmd_destroy ;;
  *) sed -n '2,27p' "$0"; exit 1 ;;
esac
