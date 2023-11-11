# Author: Jigarvarma2005

from os import environ, path
from dotenv import load_dotenv

if path.exists("config.env"):
    load_dotenv("config.env")

class Config(object):
    BOT_TOKEN = environ.get('BOT_TOKEN', "")
    API_ID = int(environ.get('API_ID', 12345))
    API_HASH = environ.get('API_HASH', "")
    MONGO_DB_URI = environ.get('MONGO_DB_URI', "")