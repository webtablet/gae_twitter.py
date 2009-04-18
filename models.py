#import datetime
# -*- coding: utf-8 -*-
from google.appengine.ext import db
import feedparser
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
                           auto_current_user=True, auto_current_user_add=True)
    link = db.LinkProperty(verbose_name="Link to the bot website")
    feed = db.LinkProperty(verbose_name="Feed URL", required=True)
    desc = db.TextProperty(verbose_name="Description of the bot")
    message = db.TextProperty(verbose_name="message post to twitter",
                              default="{{title}} : {{url}}")
    status = db.TextProperty(verbose_name="Error messages")

    updated = db.DateTimeProperty(verbose_name="The time this bot is updated",
                                  auto_now=True)
    created = db.DateTimeProperty(verbose_name="The time this bot is created",
                                  auto_now_add=True)

    def create_post_message(self, entry):
        message = self.message
        message = message.replace('{{title}}',
                                  entry.get('title', "No title").encode('utf-8'))
        message = message.replace('{{link}}',
                                  entry.get('link', "No link").encode('utf-8'))
        message = message.replace('{{author}}',
                                  entry.get('author', "No author").encode('utf-8'))
        return message

    def postfeedentry(self, last_update):
        gae_twitter = GAETwitter(username=self.name, password=self.password)
        feed_result = feedparser.parse(self.feed)
        if 'bozo_exception' in feed_result:
            self.status = str(feed_result.bozo_exception)
            self.put()
            return False
        self.put()
        if not ("entries" in feed_result):
            return False
        for entry in feed_result.entries:
            entry_time = entry.get("updated", None)
#            entry_time = localtime(mktime(email.Utils.parsedate(entry_date)) + 32400)
#            entry_time = strftime('%Y/%m/%d %H:%M',entry_date)
            if not entry_time:
                continue
#            if entry_time < last_update:
#                continue
            message = self.create_post_message(entry)
            status = gae_twitter.post(message)
            self.status = status


def bots_by_user(user):
    return db.GqlQuery("SELECT * FROM Bot WHERE user = :1",
                       user)


def bots_to_update():
    return db.GqlQuery("SELECT * FROM Bot WHERE enable = :1 LIMIT 1",
                       True)
