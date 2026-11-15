Run `make migrate` from the repository root to apply revisions to the configured database. The URL comes from settings/environment, never from a checked-in credential file. Revision `0001_initial_schema` creates the domain tables and the `btree_gist` extension for confirmed-booking overlap protection.

Migrations contain their own schema definitions and do not import the current models. Never use `create_all()` as a substitute for migrations. `make schema-check` checks model/migration drift, and integration tests apply migrations from zero in unique schemas on the isolated test database.

Downgrading the initial revision removes its tables and indexes. This is destructive and is not part of normal setup. The extension is deliberately retained because other schemas may depend on it. No migration or seed is executed at API startup.
