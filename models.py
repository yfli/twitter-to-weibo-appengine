
from google.appengine.ext import db

class Account(db.Model):
    tw_account = db.StringProperty()
    tw_token = db.StringProperty()
    tw_last_msg_id = db.StringProperty()
    wb_account = db.StringProperty()
    wb_passwd = db.StringProperty()
