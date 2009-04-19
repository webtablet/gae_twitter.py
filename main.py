#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#

import os
import sys
import time
import logging

from os.path import dirname, join as join_path


import wsgiref.handlers

# Why epylint.py doesnot recognize the webapp module?
# /Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/google/appengine/ext/webapp

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.webapp import template


APP_DIRECTORY = dirname(__file__)
sys.path.insert(0, join_path(APP_DIRECTORY, 'third_party'))

INVALID_ACCOUNT = 1
INVALID_FEED = 2

# I use relative imports...
from gae_twitter import GAETwitter
from models import Bot, bots_by_user, bots_to_update

import feedparser

from twitter_password import TWITTER_USERNAME, TWITTER_PASSWORD

def debug(message):
    """Debug function using logging module"""
    logging.getLogger().debug(message)

def template_path(name):
    """Absolute path to a template file"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    return os.path.join(template_dir, (name + ".html"))

class MainHandler(webapp.RequestHandler):
    """Top page"""
    def get(self):
        user = users.get_current_user()
        bots = bots_to_update()
        template_values = {}
        if user:
            template_values = {
                'username': user.nickname(),
                'useremail': user.email(),
                'logout_url': users.create_logout_url("/"),
                'bots' : bots,
                }
        else:
            template_values = {
                'login_url': users.create_login_url("/"),
                'bots' : bots,
                }
        path = template_path("index")
        self.response.out.write(template.render(path, template_values))
#        self.response.out.write("top page")

class BotCreateHandler(webapp.RequestHandler):
    """A handler that creates a Bot"""
    def post(self):
        """Creates a bot"""
        error_status = 0
        user = users.get_current_user()
        if not user:
            self.response.out.write("not registered in google")
        name = self.request.get('name')
        password = self.request.get('password')
        feed = self.request.get('feed')

        # Verify the account information
        gae_twitter = GAETwitter(username=name, password=password)
        verify_result = gae_twitter.verify()
        if (verify_result != True):
            error_status = error_status + 1

        # Verify the feed URL
        d = feedparser.parse(feed)

        if (d.bozo > 0):
            error_status = error_status + 2

        if (error_status == 0):
            bot = Bot(name=name, password=password, feed=feed)
            bot.user = user
            bot.put()
        self.response.out.write(str(error_status))


    def get(self):
        self.response.out.write("post me!")

class BotEditHandler(webapp.RequestHandler):
    def post(self):
        """Edits a bot"""
        key = self.request.get('key')
        bot = db.get(db.Key(key))
        try:
            bot.update_myself(self.request)
        except Exception, e:
            self.response.out.write(str(e))
            return
        self.response.out.write("0")

    def get(self):
        key = self.request.get('key')
        bot = Bot.get(key)
        template_values = {
            'bot': bot,
            'logout_url': users.create_logout_url("/"),
            }
        path = template_path("edit")
        self.response.out.write(template.render(path, template_values))


class BotShowHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            greeting = ("<a href=\"%s\">Sign in or register</a>." %
                        users.create_login_url("/"))
            self.response.out.write("<html><body>%s</body></html>" % greeting)
            return
        bots = bots_by_user(user)
        template_values = {
            'bots': bots,
            'logout_url': users.create_logout_url("/"),
            }
        path = template_path("show")
        self.response.out.write(template.render(path, template_values))

class BotCronHandler(webapp.RequestHandler):
    """Cron job handler of bots"""
    def get(self):
        bots = bots_to_update()[:1]
        feeds = ""
        for bot in bots:
            logging.debug(bot.name)
            feeds = feeds + bot.feed + "\n"
            post_count = bot.postfeedentry()
        self.response.out.write(feeds + str(post_count))


def main():
    application = webapp.WSGIApplication(
        [('/', MainHandler),
         ('/create/', BotCreateHandler),
         ('/show/', BotShowHandler),
         ('/edit/', BotEditHandler),
         ('/cron/', BotCronHandler)],
        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
