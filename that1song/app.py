from flask import Flask, render_template, redirect, request, session, url_for, send_from_directory
from flask_session import Session
from waitress import serve
import config
import random
import os
import re
import urllib
from spotify import Spotify
import examples


# Setup the flask application.
# All setting come from environment variables.
app = Flask(__name__)
app.config.from_object('config')
Session(app)

spotify = Spotify(
    config.SPOTIFY_CLIENT_ID, 
    config.SPOTIFY_CLIENT_SECRET)


# Index page shows the form to enter a song name.
# It also handles to post back from the form.
@app.route('/')
def index():
    
    # If the user clicked search there will be an 's' argument
    search = request.args.get('s')
    if not search:
        # No argument so show the form
        return render_template('search.html', error=session.pop('error', None))

    # We will filter songs so we search for many more than we want.
    songs = spotify.get_songs(search, config.MAX_SONGS * 10)    

    if not (songs and len(songs)):
        # There are not songs.
        return render_template('nosongs.html', examples=random.sample(examples.searches, 4))

    songs.sort(key = lambda item: item['popularity'], reverse = True)

    # Only allow 1 song from each artist.
    top_songs = []
    found_artists = []
    
    for song in songs:
        artists = song['artists']
        if artists in found_artists:
            continue

        found_artists.append(artists)
        top_songs.append(song)

        if len(top_songs) == config.MAX_SONGS:
            break

    # Show the songs.
    return render_template('songs.html', search=search, songs=top_songs)


# Handles when the user clicks the Add button on the list of songs.
@app.route('/add', methods=['POST'])
def add():
    name = request.form['s']
    song_ids = request.form.getlist('song_id')

    # Get the user we are going to add the playlist for.
    spotify_user = spotify.get_user()
    if not spotify_user:
        # We don't have an authenticated spotify user so do authentication now.
        # Before we do that, remember what they are adding.
        # There is a race condition if the same browser is clicking add on two different tabs
        # at the same time, but I don't care.
        session['add'] = { 'name': name, 'song_ids': song_ids }
        return redirect(spotify.get_authorize_url(config.AUTHORIZE_CALLBACK))

    # Make the playlist.
    playlist_id = spotify.make_playlist(spotify_user, _titlecase(name), song_ids)

    # Show the results using the Post/Redirect/Get pattern.
    return redirect('/added?id=' + playlist_id)


# Display a playlist which has been added.
@app.route('/added')
def added():
    playlist_id = request.args.get('id')

    # We need the user to show them their playlist
    spotify_user = spotify.get_user()
    if not spotify_user:
        # Its possible this page was opened after the user no longer has a session,
        # Just redirect to the search page
        return redirect('/')

    # Get and show the playlist
    playlist = spotify.get_playlist(spotify_user, playlist_id)
    return redirect(playlist['url'])


# Spotify redirects here after a user has been authorized
# Note, this URL has to be regestered with Spotify.
# TODO - THe user can cancel authorization.
@app.route('/authorize')
def authorize():
    error = request.args.get('error')
    code = request.args.get('code')

    if error or not code:
        session['error'] = \
            "Oh No! We can't access your Spotify account. " \
            "You can still search for lists of songs. " \
            "We just can't make a playlist for you."
        return redirect('/')

    spotify.authorize(code, config.AUTHORIZE_CALLBACK)

    # If the user had to authorize wile adding a playlist then do that now.
    add = session.pop('add')
    if add:
        spotify_user = spotify.get_user()
        playlist_id = spotify.make_playlist(spotify_user, _titlecase(add['name']), add['song_ids'])
        # Show the results
        return redirect('/added?id=' + playlist_id)

    redirect('/')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# Title case a string.
def _titlecase(text):
    text = re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda match: match.group(0).capitalize(), text)
    text = re.sub('\s+The\s+', ' the ', text)
    text = re.sub('\sOf\s', ' of ', text)
    text = re.sub('\sA\s', ' a ', text)
    return text


@app.template_filter('quote_plus')
def quote_plus(text):
    return urllib.parse.quote_plus(text)


if __name__ == '__main__':
    if config.FLASK_ENV == 'production':
        serve(app, host='0.0.0.0', port=5000)
    else:
        app.run(debug=True)
