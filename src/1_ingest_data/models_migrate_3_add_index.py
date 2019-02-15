from peewee import SqliteDatabase
from playhouse.migrate import SqliteMigrator, migrate

db = SqliteDatabase('/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/artworks.sqlite3')
migrator = SqliteMigrator(db)

migrate(
    # Create a unique index
    migrator.add_index('image', ('img_local_path',), True),
)
