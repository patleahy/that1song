from os import environ

FLASK_ENV               = environ.get("FLASK_ENV")
SECRET_KEY              = environ.get("FLASK_SECRET_KEY")
SPOTIFY_CLIENT_ID       = environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET   = environ.get("SPOTIFY_CLIENT_SECRET")

SESSION_TYPE = 'filesystem' # TODO Use something else
SESSION_TIMEOUT_MINUTES = 30 # Spotify tokens timeout in 60 min.
AUTHORIZE_CALLBACK = "https://that1song.com/authorize"

# The number of songs to return in searches.
MAX_SONGS = 32
