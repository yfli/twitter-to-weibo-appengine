
from google.appengine.ext import db

class Account(db.Model):
    tw_token_key = db.StringProperty()
    tw_token_secret = db.StringProperty()
    tw_access_key = db.StringProperty()
    tw_access_secret = db.StringProperty()
    tw_last_msg_id = db.StringProperty()
    wb_account = db.StringProperty()
    wb_passwd = db.StringProperty()
    wb_gtalk_bot = db.StringProperty()

class OAuthToken(db.Model):
    token_key = db.StringProperty(required=True)
    token_secret = db.StringProperty(required=True)

