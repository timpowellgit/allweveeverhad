import tweepy
import os
 
# Consumer keys and access tokens, used for OAuth
consumer_key = 'LXKZWn4MvwNHWo2mtg271lVGd'
consumer_secret = '5USbdkUTPQPxG7vrNclKXRTW2pPtLNmbVAD6KGWde1yrHud1ZU'
access_token = '987783701764411393-X0S32xbqr9nbUgPvXY9iVLOWejV3idH'
access_token_secret = 'tnEfPae5M2HQLT3qTa570vQq4PiX9FPW2FVfIqUJcUNKP'

IMG_PATH = '/Users/greg/Desktop/ART-freeriots/adam-basanta-all-weve-ever-had-is-one-another/repo/src/5_installation/_test/twitter/scan.jpg'
 
# OAuth process, using the keys and tokens
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
 
# Creation of the actual interface, using authentication
api = tweepy.API(auth)

# Creates the user object. The me() method returns the user whose authentication keys were used.
user = api.me()
 
print('Name: ' + user.name)
print('Location: ' + user.location)
print('Friends: ' + str(user.friends_count))
 
# Sample method, used to update a status
# api.update_status('Hello Form RBI Lab!')

# load image
imagePath = "img.jpg"
status = "Hi! From Python script=) #hash #tag"

# Send the tweet.
api.update_with_media(IMG_PATH, status)
