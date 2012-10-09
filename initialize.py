#!/usr/bin/env python
# -*- coding: utf-8 -*-

#to ensure the utf8 encoding environment
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)
import time
from google.appengine.ext import db
from google.appengine.api import xmpp

from myid import my_weibo_bot, my_weibo_bot_verify_code


def initialize():
    #do something to initialize.
    xmpp.send_invite(my_weibo_bot)
    xmpp.send_message(my_weibo_bot, my_weibo_bot_verify_code)

initialize()
print "<html><body>"
print "</body></html>"
