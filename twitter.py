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
import simplejson as json

from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.api import xmpp

from poster.encode import multipart_encode, MultipartParam
import tweepy
from tweepy.error import TweepError

from myid import *
from models import Account

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

def untco_tcoonly(url):
    try:
        logging.debug("Fall back to TCO only unshort %s", url)
        response = urlfetch.fetch(url,
                method=urlfetch.HEAD, follow_redirects=False)
        return response.headers['location']
    except:
        logging.debug("Error tco-only unshort %s", url)
        traceback.print_exc(file=sys.stdout)
        return url

def untco(url):
    try:
        response = urlfetch.fetch(url,
                method=urlfetch.HEAD)
    except:
        logging.debug("Error redirect unshort %s", url)
        traceback.print_exc(file=sys.stdout)
        return untco_tcoonly(url)

    if not response.final_url.startswith("http://"):
        return untco_tcoonly(url)

    return response.final_url

def short_tinycc(longurl):
    url = "http://tiny.cc/?c=rest_api&m=shorten&version=2.0.3&format=xml&longUrl=%s&login=%s&apiKey=%s"%(urllib.quote_plus(longurl),MY_TINYCC_LOGIN,MY_TINYCC_APIKEY)
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

def short_tinycc_json(longurl):

    url = "http://tiny.cc/?c=rest_api&m=shorten&version=2.0.3&format=json&longUrl=%s&login=%s&apiKey=%s"%(urllib.quote_plus(longurl),MY_TINYCC_LOGIN,MY_TINYCC_APIKEY)

    try:
        result = urlfetch.fetch(url)
        if result.status_code != 200:
            raise RuntimeError("tinycc returns non-200")
        jr = json.loads(result.content)
        if jr.get("results") :
            return jr.get("results").get("short_url")
        else:
            raise RuntimeError("tiny.cc return error - "+jr.get("errorMessage"))
    except Exception, err:
        logging.error("Error:%s"%str(err))
        return None

def get_img_file_url(img_site_url):
    if not (img_site_url.startswith("http://flic.kr") or 
            img_site_url.startswith("http://www.flickr.com/photos") or 
            img_site_url.startswith("http://instagr.am") or 
            img_site_url.startswith("http://instagram.com") or 
            img_site_url.startswith("http://yfrog.com") or 
            img_site_url.startswith("http://littlemonsters.com/image") or 
            img_site_url.startswith("http://picplz.com") or
            img_site_url.startswith("http://twitter.com") or 
            img_site_url.startswith("http://twitpic.com") or 
            img_site_url.startswith("http://img.ly") 
            ) :
        logging.debug("Not a supported img site:%s", img_site_url)
        return None

    try:
        response = urlfetch.fetch(img_site_url)
        if response.status_code != 200 :
            return None

        if (img_site_url.startswith("http://flic.kr") or 
                img_site_url.startswith("http://www.flickr.com/photos")):
            # return the largest img url of flickr
            # (no more than 1024 as larger image has a different secret
            m = re.search(r"baseURL: +\'([^\']+)\'", response.content)
            if m:
                base_url = m.group(1)
            else:
                return None

            m = re.search(r"sizeMap: +\[([^<]+)\]", response.content)
            if m:
                size_map = ['_b', '_c', '_z',  '_m', '_n', '_s', '_q', '_sq', '_t']
                for size in size_map:
                    if m.group(1).find(size) != -1:
                        return base_url.replace('.jpg', size+'.jpg')
                else:
                    return base_url
            else:
                logging.debug("Do not find image file url for %s", img_site_url)
                return None

        if img_site_url.startswith("http://littlemonsters.com/image") : 
            m = re.search(r"og:image\" content=\"([^<]+)\"", response.content)
            if m:
                return m.group(1).replace("_200.","_700.")
            else:
                return None
                
        if (img_site_url.startswith("http://instagr.am") or 
                img_site_url.startswith("http://instagram.com") or 
                img_site_url.startswith("http://yfrog.com") or 
                img_site_url.startswith("http://littlemonsters.com/image") or 
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
            m = re.search(r"pbs\.twimg\.com/media/([^<]+)\.jpg", response.content)
            if m:
                return "http://pbs.twimg.com/media/"+m.group(1)+".jpg:large"
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
    t = re.findall(r"(http://t\.co/\w+)", msg)
    img_file_url = None
    for orig in t:
        expanded = untco(orig)
        logging.debug("expanded: %s", expanded)
        if img_file_url == None:
            img_file_url = get_img_file_url(expanded)
        reshortened = short_tinycc_json(expanded)
        logging.debug("reshort: %s", reshortened)
        if reshortened != None:
            msg = msg.replace( orig, reshortened)
        else:
            if expanded.startswith("http://t.co"):
                expanded = "ForbidenURL"
            msg = msg.replace(orig, expanded)
    logging.debug("img url: %s", img_file_url)
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
    xmpp.send_presence(MY_WEIBO_BOT)
    time.sleep(0.1)
    xmpp.send_message(MY_WEIBO_BOT, msg)

def send_sina_msg_withpic(username,password,msg, pic=None):

    logging.debug("Send to Sina: %s", msg)

    header = {}

    payload_data = {}
    payload_data['source'] = MY_WEIBO_APIKEY
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
def sync_twitter(twitter_id):

    account = Account.get_by_key_name(twitter_id)
    if account is None:
        return

    last_id = account.tw_last_msg_id

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_request_token(account.tw_token_key, account.tw_token_secret)
    auth.set_access_token(account.tw_access_key, account.tw_access_secret)

    twitter = tweepy.API(auth)

    try:
        user_timeline = twitter.user_timeline(screen_name=account.key().name(), since_id=last_id)
    except TweepError, e:
        if (e.response != None and e.response.status != 400):
            logging.error("Error to get twitter user_timeline, E: %s",e.reason)
        return;

    print "<html><body><ol>"
    for tweet in reversed(user_timeline):
        twid=tweet.id_str
        text = unescape(tweet.text)
        text, img_url = replace_tco(text)

        if text[0] == '@' : #do not sync iff @, sync RT@
            continue

        print "<li>",twid,text,"</li><br />\n"
        logging.debug("msg id=%s,msg:%s "%(twid, text))
        #send_sina_msg_withpic(MY_WEIBO_USERNAME,MY_WEIBO_PASSWORD,text, pic=img_url)
        send_sina_msg_gtalkbot(text)

        last_id = tweet.id_str

    account.tw_last_msg_id = last_id
    account.put()

    print "</ol></body></html>"
    print ""

sync_twitter(twitter_id=MY_TWITTER_ID)
