from peewee import SqliteDatabase
from playhouse.migrate import SqliteMigrator, migrate

db = SqliteDatabase('/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/artworks.sqlite3')
migrator = SqliteMigrator(db)

migrate(
  migrator.drop_column('artwork', 'source_img_url'),
  migrator.drop_column('artwork', 'img_local_path'),
)
