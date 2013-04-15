#!/usr/bin/env python
# -*- coding: utf-8 -*-

#to ensure the utf8 encoding environment
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)
import traceback
import logging
import re
import time
import htmlentitydefs
import urllib
import json

from google.appengine.api import urlfetch
from google.appengine.api import xmpp

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

def short_cbsso(longurl):

    url = "http://cbs.so/?module=ShortURL" \
            "&file=Add&mode=API&url=%s"%(urllib.quote_plus(longurl))

    try:
        result = urlfetch.fetch(url)
        while result.final_url != None: #if 302 we need again fetch the final url
            logging.debug("302, fetch again:"+result.final_url)
            result = urlfetch.fetch(result.final_url)
        if result.status_code != 200:
            raise RuntimeError("cbsso returns non-200")
        shorturl = result.content
        if shorturl.startswith('http://cbs.so'):
            return shorturl
        else:
            raise RuntimeError("cbsso wrong content" + shorturl )
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
            m = re.search(r"pbs\.twimg\.com/media/([^<]+?):large", response.content)
            if m:
                return "http://pbs.twimg.com/media/"+m.group(1)
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
        reshortened = short_cbsso(expanded)
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


def send_sina_msg_gtalkbot(account, msg):
    xmpp.send_presence(account.wb_bot_sina, from_jid=account.wb_bot_mine)
    time.sleep(5)
    xmpp.send_message(account.wb_bot_sina, msg, from_jid=account.wb_bot_mine)

#get one page of to user's replies, 20 messages at most. 
def sync_twitter(account):

    if account is None:
        return

    last_id = account.tw_last_msg_id
    last_msg = account.tw_last_msg

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_request_token(account.tw_token_key, account.tw_token_secret)
    auth.set_access_token(account.tw_access_key, account.tw_access_secret)

    twitter = tweepy.API(auth)

    try:
        user_timeline = twitter.user_timeline(
            screen_name=account.tw_screenname, since_id=last_id, count=5)
    except TweepError, e:
        if (e.response != None and e.response.status != 400):
            logging.error("Error to get twitter %s user_timeline, E: %s",
                account.tw_screenname,e.reason)
        return;

    for tweet in reversed(user_timeline):
        twid=tweet.id_str
        text = unescape(tweet.text)
        text, img_url = replace_tco(text)

        if text[0] == '@' : #do not sync iff @, sync RT@
            continue

        logging.debug("msg id=%s,msg:%s "%(twid, text))
        send_sina_msg_gtalkbot(account, text)

        last_id = tweet.id_str
        last_msg = text

    account.tw_last_msg_id = last_id
    account.tw_last_msg = last_msg
    account.put()

for account in Account.all():
    sync_twitter(account)

