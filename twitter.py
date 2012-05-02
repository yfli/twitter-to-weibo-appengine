#!/usr/bin/env python
# -*- coding: utf-8 -*-

#to ensure the utf8 encoding environment
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)
import traceback
import base64
import logging
import re
import htmlentitydefs
import time
import urllib,urllib2,Cookie
from google.appengine.api import urlfetch
from google.appengine.ext import db

my_twitter_id="you"
my_weibo_username="yourid@sina.com"
my_weibo_password="yourpassword"
my_weibo_apikey=1234567890 
my_tinycc_login="yourlogin"
my_tinycc_api_key="yourapikey"

class Twitter(db.Model):
    id=db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)

def make_cookie_header(cookie):
    ret = ""
    for val in cookie.values():
        ret+="%s=%s; "%(val.key, val.value)
    return ret

def unescape(text):
   """Removes HTML or XML character references 
      and entities from a text string.
   from Fredrik Lundh
   http://effbot.org/zone/re-sub.htm#unescape-html
   """
   def fixup(m):
       text = m.group(0)
       if text[:2] == "&#":
           # character reference
           try:
               if text[:3] == "&#x":
                   return unichr(int(text[3:-1], 16))
               else:
                   return unichr(int(text[2:-1]))
           except ValueError:
               pass
       else:
           # named entity
           try:
               text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
           except KeyError:
               pass
       return text # leave as is
   return re.sub("&#?\w+;", fixup, text)

def getLatest():
    msg=db.GqlQuery("SELECT * FROM Twitter ORDER BY created DESC")
    x=msg.count()
    if x:
        return msg[0].id
    else:
        return ""

def deleteData(since_id):
    if since_id:
        q = db.GqlQuery("SELECT * FROM Twitter Where id < :1", since_id) 
        results = q.fetch(100) 
        db.delete(results)
        return True
    else:
        return False

def send_sina_msgs(username,password,msg):
    auth=base64.b64encode(username+":"+password)
    auth='Basic '+auth
    msg=unescape(msg)
    logging.debug("Send to Sina: %s", msg)
    form_fields = {
            "status": msg,
            }
    form_data = urllib.urlencode(form_fields)
    result = urlfetch.fetch(url="http://api.t.sina.com.cn/statuses/update.xml?source=%s"%my_weibo_apikey,
            payload=form_data,
            method=urlfetch.POST,
            headers={'Authorization':auth}
            )
    if result.status_code == 200:
        bk=result.content
        if bk.find("true"):
            return True
    else:
        return False

def send_sina_web_msgs(username,password,msg):
        # send sina msgs. use sina username, password.
        # the msgs parameter is a message list, not a single string.       
        result = urlfetch.fetch(url="https://login.sina.com.cn/sso/login.php?username=%s&password=%s&returntype=TEXT"%(username,password))
        cookie = Cookie.SimpleCookie(result.headers.get('set-cookie', ''))
        msg=unescape(msg)
        form_fields = {
          "content": msg,          
        }
        form_data = urllib.urlencode(form_fields)

        result = urlfetch.fetch(url="http://t.sina.com.cn/mblog/publish.php",
                            payload=form_data,
                            method=urlfetch.POST,
                            headers={'Referer':'http://t.sina.com.cn','Cookie' : make_cookie_header(cookie)})
        #print ""
        #print result.content
        

def untco(url):
    try:
        response = urlfetch.fetch(url,
                method=urlfetch.HEAD)
    except:
        logging.debug("Error unshort %s", url)
        traceback.print_exc(file=sys.stdout)
        return url

    return response.final_url

def short_tinycc(longurl):
    url = "http://tiny.cc/?c=rest_api&m=shorten&version=2.0.3&format=xml&longUrl=%s&login=%s&apiKey=%s"%(urllib.quote_plus(longurl),my_tinycc_login,my_tinycc_api_key)
    result = urlfetch.fetch(url)
    if result.status_code == 200 :
        content = result.content
        ##print "short content", content
        errCode = re.search("<errorCode>0<", content)
        if errCode != None:
            short = re.findall(r"<shorturl>([^<]+)</shorturl>",content)
            return short[0]
    logging.debug("Error shorten %s in tinycc", longurl)
    return None



def replacetco(msg):
    t = re.findall(r"(http://t\.co/\S{8})", msg)
    for orig in t:
        expanded = untco(orig)
        logging.debug("expanded: %s", expanded)
        #print "expa: ", expanded
        reshortened = short_tinycc(expanded)
        logging.debug("reshort: %s", reshortened)
        if reshortened != None:
            msg = msg.replace( orig, reshortened)
        else:
            if expanded[:11] == "http://t.co":
                expanded = "ForbidenURL"
            msg = msg.replace( orig, expanded)
    return msg

#get one page of to user's replies, 20 messages at most. 
def parseTwitter(twitter_id,since_id="",):
    if since_id:
        url="http://twitter.com/statuses/user_timeline/%s.xml?since_id=%s"%(twitter_id,since_id)
    else:
        url="http://twitter.com/statuses/user_timeline/%s.xml"%(twitter_id)
    #print url
    #logging.debug("start logging, %s ", url)
    result = urlfetch.fetch(url)
    #print result.content
    if result.status_code == 200:
        content = result.content
        m = re.findall(r"(?i)<id>([^<]+)</id>\s*<text>(?!@)([^<]+)</text>", content)
        #logging.debug("xml content ", content)
        print "<html><body><ol>"
        for x in reversed(m):
            id=x[0]
            text=replacetco(x[1])
            #print "message: ",text
            if text[0] != '@' : #only not sync @, sync RT
                print "<li>",id,text,"</li><br />\n"
                logging.debug("msg id=%s msg:%s ", id, text )
                send_sina_msgs(my_weibo_username,my_weibo_password,text)
                msg=Twitter()
                msg.id=id
                msg.put()
        print "</ol></body></html>"
    else:
        print "get twitter data error. "
        print result.content

    print ""

latest=getLatest() 
# deleteData(since_id=latest)
parseTwitter(twitter_id=my_twitter_id,since_id=latest)
#parseTwitter(twitter_id=my_twitter_id)
