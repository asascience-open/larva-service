import os

DEBUG = False
TESTING = False

SECRET_KEY = os.environ.get("SECRET_KEY")

LOG_FILE = bool(os.environ.get("LOG_FILE"))
