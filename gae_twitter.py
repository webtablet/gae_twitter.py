#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
r""" A Twitter client class for Google App Engine.
This Python module implements a twitter (http://twitter.com/) client,
which can work in Google App Engine (http://code.google.com/appengine/).

Once the instance created with twitter username and password,
it can tweet message.

todo:
    appropriate error handling
    tests?
    to get messages
    to get friends information

This module is developped mainly for studying Python.
Any advice (the zen of python, architecture of class, writing in English)
for this module and me is very welcomed.

"""

__author__ = "Suzuki Tomohiro <http://twitter.com/suztomo>"
__date__ = "2009-04-18"
__version__ = "0.0.1"

# Imports should be grouped in the following order:
#      1. standard library imports
#      2. related third party imports
#      3. local application/library specific imports

# standard library
import urllib
import base64

# third party
from google.appengine.ext import webapp
from google.appengine.api import urlfetch


#
# global constants

TWITTER_POST_PROTOCOL="http"
TWITTER_SITE = "twitter.com"
TWITTER_POST_PATH = "/statuses/update.rss"
TWITTER_POST_URL = "%s://%s%s" % (TWITTER_POST_PROTOCOL, TWITTER_SITE,
                                  TWITTER_POST_PATH)
# => http://twitter.com/statuses/update.rss

class GAETwitter(object):
    """Twitter class that communicates with twitter.com

    """
    def __init__(self, username, password):
        """initializes the class with username and password
        """
        self.username = username  # username used for login
        self.password = password  # password used for login

    def post(self, message):
        """posts the message
        returns the status code from the post
        """
        form_fields = {
          "status": message,
           }
        form_data = urllib.urlencode(form_fields)
        base64string = base64.encodestring("%s:%s" % (
                self.username, self.password))[:-1]
        headers = {
            "Authorization": ("Basic %s" % base64string),
            'Content-Type': 'application/x-www-form-urlencoded'
            }
        try:
            response = urlfetch.fetch(url=TWITTER_POST_URL,
                                payload=form_data,
                                method=urlfetch.POST,
                                headers=headers)
            return response.status_code
        except Exception, e:
            return False

# end file
