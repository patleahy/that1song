from os import environ

FLASK_ENV               = environ.get("FLASK_ENV")
SECRET_KEY              = environ.get("FLASK_SECRET_KEY")
SPOTIFY_CLIENT_ID       = environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET   = environ.get("SPOTIFY_CLIENT_SECRET")

SESSION_TYPE = 'filesystem' # TODO Use something else
AUTHORIZE_CALLBACK = "http://that1song.com:5000/authorize"

# The number of songs to return in searches.
MAX_SONGS = 30 