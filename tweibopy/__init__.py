# Tweepy
# Copyright 2009-2010 Joshua Roesslein
# See LICENSE for details.

"""
Tweepy Twitter API library
"""
__version__ = '1.10'
__author__ = 'Joshua Roesslein'
__license__ = 'MIT'

from tweibopy.models import Status, User, DirectMessage, Friendship, SavedSearch, SearchResult, ModelFactory
from tweibopy.error import TweepError
from tweibopy.api import API
from tweibopy.cache import Cache, MemoryCache, FileCache
from tweibopy.auth import BasicAuthHandler, OAuthHandler
from tweibopy.streaming import Stream, StreamListener
from tweibopy.cursor import Cursor

# Global, unauthenticated instance of API
api = API()

def debug(enable=True, level=1):

    import httplib
    httplib.HTTPConnection.debuglevel = level

