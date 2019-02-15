from models_utils import JSONField
from peewee import Model, CharField, IntegerField, SqliteDatabase, \
                    ForeignKeyField

# defer initialization to later
# not including this line seems to break peewee initialization...
db = SqliteDatabase(None)

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
  year = IntegerField(null=True)

  # --- meta &c. ---
  # any non-"primary" (e.g., something other than the title/artist) data;
  # anything that's source-specific as well.
  # no use for this field is foreseen for now.
  metadata = JSONField(null=True)

  class Meta:
    database = db
    # source name + id should be unique (and indexed!)
    indexes = (
      (('source_name', 'source_id'), True),
    )

class Image(Model):
  artwork_id = ForeignKeyField(Artwork, backref='images')

  # --- img ---
  # full url to the source image
  # (the highest resolution image of this work of art)
  source_img_url = CharField()

  # path to the downloaded image file on the Digital Ocean machine
  img_local_path = CharField()

  @classmethod
  def get_by_id_safe(cls, id):

    try:
      return cls.get_by_id(id)
    except cls.DoesNotExist:
      pass
      print '%s id not found, skipped' %id

  class Meta:
    database = db
    indexes = (
      (('img_local_path'), True),
    )
