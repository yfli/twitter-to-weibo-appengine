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
import time
import htmlentitydefs
import urllib,Cookie
try:
    import json
except ImportError:
    import simplejson as json

from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.api import xmpp
from poster.encode import multipart_encode, MultipartParam

import tweepy
from tweepy.error import TweepError

from testid import my_twitter_id, my_weibo_username, my_weibo_password
from testid import my_weibo_apikey, my_tinycc_login, my_tinycc_apikey
from testid import my_weibo_bot

class Twitter(db.Model):
    twid = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)

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
        return msg[0].twid
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

def untco(url):
    try:
        response = urlfetch.fetch(url,
                method=urlfetch.HEAD)
    except:
        logging.debug("Error unshort %s", url)
        traceback.print_exc(file=sys.stdout)
        return url

    if not response.final_url.startswith("http://"):
        try:
            logging.debug("Fall back to TCO only unshort %s", url)
            response = urlfetch.fetch(url,
                    method=urlfetch.HEAD, follow_redirects=False)
            return response.headers['location']
        except:
            logging.debug("Error unshort %s", url)
            traceback.print_exc(file=sys.stdout)
            return url

    return response.final_url

def short_tinycc(longurl):
    url = "http://tiny.cc/?c=rest_api&m=shorten&version=2.0.3&format=xml&longUrl=%s&login=%s&apiKey=%s"%(urllib.quote_plus(longurl),my_tinycc_login,my_tinycc_apikey)
    result = urlfetch.fetch(url)
    if result.status_code == 200 :
        content = result.content
        ##print "short content", content
        errCode = re.search("<errorCode>0<", content)
        if errCode != None:
            short = re.findall(r"<shorturl>([^<]+)</shorturl>",content)
            return short[0]
        else:
            logging.debug("tinycc Error: %s ", errCode)

    logging.debug("Error shorten %s in tinycc", longurl)
    return None

def get_img_file_url(img_site_url):
    if not (img_site_url.startswith("http://flic.kr") or 
            img_site_url.startswith("http://www.flickr.com/photos") or 
            img_site_url.startswith("http://instagr.am") or 
            img_site_url.startswith("http://yfrog.com") or 
            img_site_url.startswith("http://picplz.com") or
            img_site_url.startswith("http://twitter.com") or 
            img_site_url.startswith("http://twitpic.com") or 
            img_site_url.startswith("http://img.ly") 
            ) :
        logging.debug("Not a supported img site:%s", img_site_url)
        return None

    try:
        response = urlfetch.fetch(img_site_url)
        if response.status_code == 200 :
            if (img_site_url.startswith("http://flic.kr") or 
                    img_site_url.startswith("http://www.flickr.com/photos") or 
                    img_site_url.startswith("http://instagr.am") or 
                    img_site_url.startswith("http://yfrog.com") or 
                    img_site_url.startswith("http://picplz.com")) :
                #picplz #flickr #instgram #yfrog, standard og:image
                m = re.search(r"og:image\" content=\"([^<]+)\"", response.content)
                if m:
                    return m.group(1)
                else:
                    logging.debug("Do not find image file url for %s", img_site_url)
                    return None
            elif img_site_url.startswith("http://twitter.com") :
                #twitter.com, no og:image 
                m = re.search(r"img src=\"https://p.twimg.com/([^<]+)\"", response.content)
                if m:
                    return "http://p.twimg.com/"+m.group(1)+":large"
                else:
                    logging.debug("Do not find image file url for %s", img_site_url)
                    return None
            elif img_site_url.startswith("http://twitpic.com") :
                #twitpic small thumbnail
                #Not working
                #seems twitpic/cloudfront.net is blocking gae requests for file, 
                return "http://twitpic.com/show/large/" + img_site_url[19:]

            elif img_site_url.startswith("http://img.ly") :
                #imgly, og:image at last
                m = re.search(r"content=\"([^<]+)\" property=\"og:image\"", response.content)
                if m:
                    return m.group(1).replace("thumb", "large")
                else:
                    logging.debug("Do not find image file url for %s", img_site_url)
                    return None

    except:
        logging.debug("Error fetch image url %s", img_site_url)
        traceback.print_exc(file=sys.stdout)
        return None

def replace_tco(msg):
    t = re.findall(r"(http://t\.co/\S{8})", msg)
    img_file_url = None
    for orig in t:
        expanded = untco(orig)
        logging.debug("expanded: %s", expanded)
        if img_file_url == None:
            img_file_url = get_img_file_url(expanded)
        reshortened = short_tinycc(expanded)
        logging.debug("reshort: %s", reshortened)
        if reshortened != None:
            msg = msg.replace( orig, reshortened)
        else:
            if expanded.startswith("http://t.co"):
                expanded = "ForbidenURL"
            msg = msg.replace(orig, expanded)
    return msg, img_file_url


def get_image_data(url):
    try:
        response = urlfetch.fetch(url,
                method=urlfetch.GET)
    except:
        logging.debug("Error get image %s", url)
        traceback.print_exc(file=sys.stdout)
        return None

    if response.status_code == 200:
        return response.content
    else:
        return None


def send_sina_msg_gtalkbot(msg, pic=None):
    xmpp.send_presence(my_weibo_bot)
    time.sleep(0.1)
    xmpp.send_message(my_weibo_bot, msg)

def send_sina_msg_withpic(username,password,msg, pic=None):

    logging.debug("Send to Sina: %s", msg)

    header = {}

    payload_data = {}
    payload_data['source'] = my_weibo_apikey
    payload_data['status'] = msg

    pic_data = None
    if pic != None:
        pic_data = get_image_data(pic) 
    if pic_data != None:
        payload_data['pic'] = MultipartParam('pic', filename='abc.jpg',
                filetype='image/jpeg',
                value = pic_data)
        update_url="http://api.t.sina.com.cn/statuses/upload.xml"
        to_post, header = multipart_encode(payload_data)
    else:
        update_url="http://api.t.sina.com.cn/statuses/update.xml"
        to_post = urllib.urlencode(payload_data)

    auth=base64.b64encode(username+":"+password)
    auth='Basic '+auth
    header['Authorization']=auth

    try:
        result = urlfetch.fetch(url=update_url,
                payload="".join(to_post),
                method=urlfetch.POST,
                headers=header)
        print result.status_code
        print result.content

        if result.status_code == 200:
            return True
        else:
            logging.error("Error update the message to sina, errorcode %s", result.status_code )
            return False
    except:
        logging.debug("Error update the message to sina" )
        traceback.print_exc(file=sys.stdout)
        return False

#get one page of to user's replies, 20 messages at most. 
def parseTwitter(twitter_id,since="",):
    twitter = tweepy.API()
    try:
        if since:
            user_timeline = twitter.user_timeline(screen_name=twitter_id, since_id=since)
        else:
            user_timeline = twitter.user_timeline(screen_name=twitter_id)
    except TweepError, e:
        if (e.response != None and e.response.status != 400):
            logging.error("Error to get twitter user_timeline, E: %s",e.reason)
        return;

    print "<html><body><ol>"
    for tweet in reversed(user_timeline):
        twid=tweet.id_str
        text = unescape(tweet.text)
        text, img_url = replace_tco(text)

        if text[0] != '@' : #do not sync iff @, sync RT@
            print "<li>",twid,text,"</li><br />\n"
            logging.debug("msg id=%s,msg:%s "%(twid, text))
            #send_sina_msg_withpic(my_weibo_username,my_weibo_password,text, pic=img_url)
            send_sina_msg_gtalkbot(text)

            # always log the twitter message. Non-sense to retry if it is only gfw-ed by sina 
            msg = Twitter()
            msg.twid = twid
            msg.put()
    print "</ol></body></html>"

    print ""

latest=getLatest() 
deleteData(since_id=latest)
parseTwitter(twitter_id=my_twitter_id,since=latest)
#parseTwitter(twitter_id=my_twitter_id)
