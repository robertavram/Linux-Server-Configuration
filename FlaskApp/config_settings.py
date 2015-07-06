'''Configuration for Flask app

Important: Place your keys in the secret_keys.py module, 
           which should be kept out of version control.
'''

from utils import make_csrf_state
from secret_keys import CSRF_SECRET_KEY, SESSION_KEY


class Config(object):
    # Set secret keys for CSRF protection
    SECRET_KEY = CSRF_SECRET_KEY
    CSRF_SESSION_KEY = SESSION_KEY
    # Flask-Cache settings
    CACHE_TYPE = 'gaememcached'


class Development(Config):
    DEBUG = True
    # Flask-DebugToolbar settings
    DEBUG_TB_PROFILER_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024


class Testing(Config):
    TESTING = True
    DEBUG = True
    CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024


class Production(Config):
    DEBUG = False
    CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024