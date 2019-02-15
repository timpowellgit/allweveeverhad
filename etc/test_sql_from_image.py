from models import db, Artwork, Image

ARTWORKS_SQLITE_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/artworks.sqlite3'
db.init(ARTWORKS_SQLITE_PATH)

img = Image.select().where(
  Image.img_local_path == '/mnt/volume-nyc1-01/artsy-images/d32dm0rphc51dk.cloudfront.net/---3C8HsPGPvWinDg0pf8Q/larger.jpg'
).execute()

print len(img)
print img[0].id
