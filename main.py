#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#

import os
import time
import logging

import wsgiref.handlers

# Why epylint.py doesnot recognize the webapp module?
# /Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/google/appengine/ext/webapp



from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template

# I use relative imports...
from gae_twitter import GAETwitter
from models import Bot, bots_by_user

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
        template_values = {}
        if user:
            template_values = {
                'username': user.nickname(),
                'useremail': user.email(),
                }
        else:
            template_values = {
                'login_url': users.create_login_url("/"),
                }
        path = template_path("index")
        self.response.out.write(template.render(path, template_values))
#        self.response.out.write("top page")

class BotCreateHandler(webapp.RequestHandler):
    """A handler that creates a Bot"""
    def get(self):
        user = users.get_current_user()
        if not user:
            greeting = ("<a href=\"%s\">Sign in or register</a>." %
                        users.create_login_url("/"))
            self.response.out.write("<html><body>%s</body></html>" % greeting)
            return
        greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                    (user.nickname(), users.create_logout_url("/")))
        bot = Bot(name="testbot2",
                  user=user,
                  interval=3)
        bot.put()
        debug('put a bot into database?')
        self.response.out.write('bot created')

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
            'bots': bots
            }
        path = template_path("show")
        self.response.out.write(template.render(path, template_values))

class BotCronHandler(webapp.RequestHandler):
    """Cron job handler of bots"""
    def get(self):
        gae_twitter = GAETwitter(TWITTER_USERNAME, TWITTER_PASSWORD)
        current_time = time.strftime(u'%Y年%m月%d日 %H時%M分%S秒'.encode('utf-8'))
        status_code = gae_twitter.post("Hello, GAETwitter %s" % current_time)
        if (status_code == False):
            debug('urlfetch failed')
            self.response.out.write('urlfetch failed?')
        else:
            debug('urlfetch succeed')
            self.response.out.write('urlfetch succeed %d' % status_code)

def main():
    application = webapp.WSGIApplication(
        [('/', MainHandler),
         ('/create/', BotCreateHandler),
         ('/show/', BotShowHandler),
         ('/cron/', BotCronHandler)],
        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
