#import datetime
# -*- coding: utf-8 -*-
from google.appengine.ext import db
from datetime import datetime
import feedparser

import logging

from gae_twitter import GAETwitter

class Bot(db.Model):
    """A bot
    """
    name = db.StringProperty(verbose_name="The bot's twitter account", required=True)
    password = db.StringProperty(verbose_name="The bot's passsword", required=True)

    enable = db.BooleanProperty(verbose_name="Enable or not", default=True)
    interval = db.IntegerProperty(verbose_name="Interval minutes the bot works with",
                                  default=15)
    user = db.UserProperty(verbose_name="Google Account who created the bot",
                           required=True, auto_current_user_add=True)
    link = db.LinkProperty(verbose_name="Link to the bot website")
    feed = db.LinkProperty(verbose_name="Feed URL", required=True)
    desc = db.TextProperty(verbose_name="Description of the bot")
    message = db.TextProperty(verbose_name="message post to twitter",
                              default="{{title}} : {{url}}")
    status = db.TextProperty(verbose_name="Error messages")

    last_post = db.DateTimeProperty(verbose_name="The time this bot is updated",
                                    auto_now_add=True)

    updated = db.DateTimeProperty(verbose_name="The time this bot is updated",
                                  auto_now=True)
    created = db.DateTimeProperty(verbose_name="The time this bot is created",
                                  auto_now_add=True)

    def update_myself(self, request):
        self.name = request.get('name')
        self.password = request.get('password')
        self.message = request.get('message')
        self.interval= int(request.get('interval'))
        self.feed = request.get('feed')
        if request.get('link'):
            self.link = request.get('link')
        self.enable = bool(int(request.get('enable')))
        self.desc = request.get('desc')
        self.put()

    def create_post_message(self, entry):
        message = self.message.encode('utf-8')
        message = message.replace('{{title}}',
                                      entry.get('title', "No title").encode('utf-8'))
        message = message.replace('{{url}}',
                                  entry.get('link', "No link").encode('utf-8'))

        if 'href' in entry and entry.href.find('http://twitter.com/') == 0:
            author = entry.href[len('http://twitter.com/'):]
            if author == self.name:
                return None
            message = message.replace('{{author}}', author.encode('utf-8'))
        elif 'author' in entry:
            message = message.replace('{{author}}', entry.author.encode('utf-8'))
        logging.debug(message)
        return message

    def postfeedentry(self):
        gae_twitter = GAETwitter(username=self.name, password=self.password)
        feed_result = feedparser.parse(self.feed)
        if 'bozo_exception' in feed_result:
            self.status = str(feed_result.bozo_exception)
            logging.debug("bozo_exception")
            self.put()
            return 0
        self.put()

        if not ("entries" in feed_result):
            logging.debug("no entries? %s" % self.feed)
            self.status = "%s has no entries" % self.feed
            return 0
        post_count = 0
        last_post = self.last_post
        if not last_post:
            return 0
        for entry in feed_result.entries:
            entry_time = self.last_post
#            entry_time = localtime(mktime(email.Utils.parsedate(entry_date)) + 32400)
#            entry_time = strftime('%Y/%m/%d %H:%M',entry_date)
            if not entry_time:
                continue
#            if entry_time < last_update:
#                continue
            entry_datetime = datetime(*(entry.updated_parsed[:6]))
            if entry_datetime < last_post:
                logging.debug("passed %s" % str(entry_datetime))
                continue
            message = self.create_post_message(entry)
            if not message:
                continue
            logging.debug(message)
            status = gae_twitter.post(message)
            self.last_post = entry_datetime
            self.status = status
            if post_count == 0:
                self.put()
            post_count = post_count + 1
            if post_count > 2:
                break
        self.last_post = datetime.now()
        self.put()
        return post_count


def bots_by_user(user):
    """Returns bots the current user has"""
    return db.GqlQuery("SELECT * FROM Bot WHERE user = :1",
                       user)


def bots_to_update():
    """Returns several bots whose last_post are oldest ones"""
    return db.GqlQuery("SELECT * FROM Bot WHERE enable = :1 ORDER BY last_post ASC LIMIT 3",
                       True)
