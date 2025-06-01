# Database Migrations with Alembic (Raw SQL)

## Background & Motivation

Migrations help keep track of the db structure and changes over time. They are essential for:
- **Version Control:** Track changes to the database schema.
- **Rollback:** Easily revert to a previous state if needed.
- **Automation:** Automate the process of applying and rolling back changes.
- **Documentation:** Provide a clear history of changes made to the database schema.
- **Testing:** Facilitate testing of new features and changes without affecting the production database.
- **Data Integrity:** Ensure that the database schema is always in a valid state.
- **Future-proofing:** Prepare for future changes and enhancements to the database schema.

## Why Alembic?

Alembic is the standard migration tool for Python projects. While commonly used with SQLAlchemy ORM, it can also manage pure raw SQL migrations. Key benefits:
- Version control for schema changes
- History of upgrade/downgrade steps
- Safer, more automated upgrades
- Collaboration: mergeable migration files, less risk of schema drift

## Migration Approach

- **We will use Alembic migration scripts with raw SQL, not declarative SQLAlchemy models.**
- Each migration lives in a versioned script under `src/vmpilot/db/migrations/versions/`.
- Alembic tracks migration state in a special `alembic_version` table in the SQLite database.
- Old static schema definitions in `models.py` and `update_schema()` will be phased out (after transition).

---

## Alembic Workflow (Raw SQL)

#### 1. Install Alembic (if needed)
```bash
pip install alembic
```

#### 2. Initialize Alembic (one-time setup)
From the `src/vmpilot/db` directory:
```bash
cd src/vmpilot/db
alembic init migrations
```
This creates a `migrations/` directory with config and version scripts.

#### 3. Configure Alembic
- Edit `alembic.ini` to point to your SQLite DB URL (e.g. `sqlite:///../../yourdb.sqlite3`)
- In `env.py`, ensure it uses raw SQL migrations (not automagic ORM reflection)

#### 4. Create a Migration (Raw SQL Example)

**Using the migration script (recommended):**
```bash
./bin/migrate.sh create "create exchanges table"
```

**Using alembic directly:**
```bash
# From src/vmpilot/db directory
alembic revision -m "create exchanges table"
```

Edit the generated file in `migrations/versions/` and write raw SQL in the `upgrade()` and `downgrade()` functions, e.g.:
```python
from alembic import op

def upgrade():
    op.execute("""
    CREATE TABLE IF NOT EXISTS exchanges (
        id INTEGER PRIMARY KEY,
        chat_id TEXT,
        ...
    );
    """)

def downgrade():
    op.execute("DROP TABLE IF EXISTS exchanges;")
```

#### 5. Run Migrations

**Using the migration script (recommended):**
```bash
# From project root
./bin/migrate.sh upgrade      # upgrade to latest
./bin/migrate.sh downgrade    # downgrade one revision
./bin/migrate.sh current      # show current revision
./bin/migrate.sh history      # show migration history
```

**Using alembic directly:**
```bash
# From src/vmpilot/db directory
alembic upgrade head      # upgrade to latest
alembic downgrade -1      # downgrade one revision
alembic current           # show current revision
alembic history           # show migration history
```

#### 6. Automatic Migration Application

VMPilot automatically applies pending migrations when the application starts. This ensures the database is always up to date without manual intervention.

**For Docker installations:**
- Migrations are applied during the installation process
- No manual migration steps required

**For development:**
- Migrations are applied when the database connection is first established
- Use `./bin/migrate.sh` for manual migration management
