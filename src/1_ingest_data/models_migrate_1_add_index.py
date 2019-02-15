from peewee import SqliteDatabase
from playhouse.migrate import SqliteMigrator, migrate

db = SqliteDatabase('../artworks.sqlite3')
migrator = SqliteMigrator(db)

migrate(
    # Create a unique index
    migrator.add_index('artwork', ('source_name', 'source_id'), True),
)
