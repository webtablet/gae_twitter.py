#import datetime
from google.appengine.ext import db

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
    feed = db.LinkProperty(verbose_name="Feed URL")
    desc = db.TextProperty(verbose_name="Description of the bot")
    updated = db.DateTimeProperty(verbose_name="The time this bot is updated",
                                  auto_now=True)
    created = db.DateTimeProperty(verbose_name="The time this bot is created",
                                  auto_now_add=True)


def bots_by_user(user):
    return db.GqlQuery("SELECT * FROM Bot WHERE user = :1",
                       user)

