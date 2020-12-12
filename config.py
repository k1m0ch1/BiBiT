import ast

from datetime import date, timedelta, datetime
from os import environ

_ = environ.get

TWITTER_API_KEY=_("TWITTER_API_KEY", "")
TWITTER_API_SECRET_KEY=_("TWITTER_API_SECRET_KEY", "")
TWITTER_BEARER_TOKEN=_("TWITTER_BEARER_TOKEN", "")
TWITTER_ACCESS_TOKEN=_("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET=_("TWITTER_ACCESS_TOKEN_SECRET", "")
DISCORD_WEBHOOK_URL=_("DISCORD_WEBHOOK_URL", "")
PRIME_TIME=_("PRIME_TIME", ["01:08", "09:00", "13:00", "19:00"])
PRIME_TIME = ast.literal_eval(PRIME_TIME) if type(PRIME_TIME) == str else PRIME_TIME
SCRAPPING_TIME=_("SCRAPPING_TIME", ["01:00", "07:00", "08:45", "12:45", "18:45", "21:00"])
SCRAPPING_TIME = ast.literal_eval(SCRAPPING_TIME) if type(SCRAPPING_TIME) == str else SCRAPPING_TIME
DATA_DIR=_("DATA_DIR", "./data")

TODAY_STRING = date.today().strftime("%Y-%m-%d")
YESTERDAY_STRING = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")