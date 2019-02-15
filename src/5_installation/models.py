import datetime
import json
from peewee import Model, CharField, IntegerField, SqliteDatabase, \
                    ForeignKeyField, TextField, DateTimeField, FloatField, \
                    BooleanField

# defer initialization to later
# not including this line seems to break peewee initialization...
db = SqliteDatabase(None)

class JSONField(TextField):
  def db_value(self, value):
    return json.dumps(value)

  def python_value(self, value):
    if value is not None:
      return json.loads(value)

class Artwork(Model):
  # identifier at the source i.e.., met/moma/artsy object ID
  source_id = CharField()
  # moma, artsy, met, etc.
  source_name = CharField()
  # url of the artwork's page
  source_page_url = CharField()

  # --- artwork info ---
  title = CharField()
  artist = CharField()
  # '-1' is used as a code when no valid year has been found
  # it should have been None/null instead...
  year = IntegerField(null=True)

  # --- meta &c. ---
  # any non-"primary" (e.g., something other than the title/artist) data;
  # anything that's source-specific as well.
  # no use for this field is foreseen for now.
  # >>> completely unused for now...
  metadata = JSONField(null=True)

  class Meta:
    database = db
    indexes = (
      # unique index on (source name + id), as they should be unique
      (('source_name', 'source_id'), True),
    )

class Image(Model):
  # should not have been named 'artwork_id' as
  # ORM access is now 'img_obj.artwork_id' instead of just '.artwork'
  artwork_id = ForeignKeyField(Artwork, backref='images')

  # --- img ---
  # full url to the source image
  # (the highest resolution image of this work of art)
  source_img_url = CharField()

  # path to the downloaded image file on the Digital Ocean machine
  img_local_path = CharField()

  class Meta:
    database = db
    indexes = (
      # unique index on file paths
      (('img_local_path'), True),
    )

class InstallationImageMatch(Model):
  created_timestamp = DateTimeField(default=datetime.datetime.now)

  file_path = CharField()
  image = ForeignKeyField(Image, backref='installation_matches')

  match_score = FloatField()

  # a non-None value will indicate that it was posted to twitter
  # using 'automatic' in the field names to emphasize that post/print
  # was done as part of 'normal' matching process
  twitter_post_id = CharField(null=True)
  posted_to_web_timestamp = DateTimeField(null=True)
  printed_timestamp = DateTimeField(null=True)

  class Meta:
    database = db

class InstallationConfiguration(Model):
  created_timestamp = DateTimeField(default=datetime.datetime.now)

  key = CharField()
  # will need to cast to & from type, depending on config value
  value = CharField()

  class Meta:
    database = db
