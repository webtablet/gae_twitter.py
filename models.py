#!/usr/bin/env python
# -*- coding: utf-8 -*-
from google.appengine.ext import db
from datetime import datetime
import feedparser

import logging

from gae_twitter import GAETwitter

import sgmllib

class Stripper(sgmllib.SGMLParser):
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)

    def strip(self, some_html):
        self.theString = ""
        self.feed(some_html)
        self.close()
        return self.theString

    def handle_data(self, data):
        self.theString += data

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
    exkeywords = db.TextProperty(verbose_name="keywords not to tweet",
                                    default="")

    status = db.TextProperty(verbose_name="Error messages")

    last_post = db.DateTimeProperty(verbose_name="The time this bot is updated",
                                    auto_now_add=True)

    updated = db.DateTimeProperty(verbose_name="The time this bot is updated",
                                  auto_now=True)
    created = db.DateTimeProperty(verbose_name="The time this bot is created",
                                  auto_now_add=True)

    def update_myself(self, request):
        """Updates myself using http request dictionary"""
        self.name = request.get('name')
        self.password = request.get('password')
        self.message = request.get('message')
        self.exkeywords = request.get('exkeywords')
        self.interval= int(request.get('interval'))
        self.feed = request.get('feed')
        if request.get('link'):
            self.link = request.get('link')
        self.enable = bool(int(request.get('enable')))
        self.desc = request.get('desc')
        self.put()

    def create_post_message(self, entry):
        """Creates a string used in tweet"""
        message = self.message.encode('utf-8')
        message = message.replace('{{title}}',
                                      entry.get('title', "No title").encode('utf-8'))
        message = message.replace('{{url}}',
                                  entry.get('link', "No link").encode('utf-8'))

        if message.find('{{content}}') >= 0:
            stripper = Stripper()
            stripped_content = stripper.strip(entry['content'][0]['value'].
                                              encode('utf-8'))
            message = message.replace('{{content}}',
                                      stripped_content)
            logging.debug(message)

        # Do not post if the message has exclusive keywords
        for exkeyword in self.exkeywords.split(' '):
            if len(exkeyword) < 1:
                continue
            if message.find(exkeyword.encode('utf-8')) >= 0:
                return None

        if 'href' in entry and entry.href.find('http://twitter.com/') == 0:
            author = entry.href[len('http://twitter.com/'):]
            # Do not post if the author is the bot itself
            if author == self.name:
                return None
            message = message.replace('{{author}}', author.encode('utf-8'))
        elif 'author' in entry:
            message = message.replace('{{author}}', entry.author.encode('utf-8'))
        return message

    def changestatus(self, newstat):
        self.status = newstat
        logging.debug("%s(%s) has changed status : %s" % (self.name,
                                                          self.feed,
                                                          self.status))
        self.put()

    def postfeedentry(self):
        """Posts a tweet, returns the number of tweets"""
        gae_twitter = GAETwitter(username=self.name, password=self.password)
        feed_result = feedparser.parse(self.feed)
        if 'bozo_exception' in feed_result:
            self.changestatus(str(feed_result.bozo_exception))
            logging.debug("bozo_exception : %s" % self.status)
            return 0
        # Record current time
        self.put()

        if not ("entries" in feed_result):
            self.changestatus("%s has no entries" % self.feed)
            return 0
        post_count = 0
        last_post = self.last_post
        newest_entry_datetime = last_post
        if not last_post:
            return 0
        for entry in feed_result.entries:
            # Check the entry's time
            if not 'updated_parsed' in entry:
                self.changestatus("No attribute 'updated_parsed' in %s"
                                  % (str(entry)))
                return 0
            entry_datetime = datetime(*(entry.updated_parsed[:6]))
            if entry_datetime <= last_post:
                continue
            if entry_datetime > newest_entry_datetime:
                newest_entry_datetime = entry_datetime

            message = self.create_post_message(entry)
            if not message:
                continue

            # post to twitter
            logging.debug(message)
            status = gae_twitter.post(message)
            self.status = status
            if post_count == 0:
                self.put()
            post_count = post_count + 1
            if post_count > 2:
                break
        self.last_post = newest_entry_datetime
        if post_count == 0:
            newstatus = "No new entries at %s" % str(datetime.now())
        else:
            newstatus = "Posted %d entries at %s" % (post_count,
                                                       str(datetime.now()))
        self.changestatus(newstatus)
        return post_count


def bots_by_user(user):
    """Returns bots the current user has"""
    return db.GqlQuery("SELECT * FROM Bot WHERE user = :1",
                       user)



def bots_to_update():
    """Returns several bots whose last_post are oldest ones"""
    return db.GqlQuery("SELECT * FROM Bot WHERE enable = :1 ORDER BY updated ASC LIMIT 3",
                       True)
