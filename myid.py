"""
IDs
"""
import os

if os.environ.get('SERVER_SOFTWARE','').startswith('Devel'):
    CONSUMER_KEY = 'owRilZIiE0IMHtm6Zjgfg'
    CONSUMER_SECRET = 'ES7fSj3Tw5F6HF7BvouksJ9f9Pw5ZHYek4XBRsUcic'
    CALLBACK = 'http://127.0.0.1:8080/oauth/callback'
else:
    CONSUMER_KEY = 'FsDebaMWF0LEi9TDDUofiA'
    CONSUMER_SECRET = '2q3BF3pZj5jr81MP2EZoETRTAp3AA890zEtptXI'
    CALLBACK = 'http://urfatu-tw-weibo.appspot.com/oauth/callback'

