from rauth import OAuth2Service
from flask import session
from flask_session import Session
import json
import re


# Spotify API Wrapper
class Spotify:

    def __init__(self, client_id, client_secret):
        self.oauth = OAuth2Service(
            name='spotify',
            client_id=client_id,
            client_secret=client_secret,
            base_url='https://api.spotify.com/v1/',
            authorize_url='https://accounts.spotify.com/authorize',
            access_token_url='https://accounts.spotify.com/api/token')

        token = self.oauth.get_access_token(
            decoder = Spotify.utf8_json_decoder,
            data = { "grant_type": "client_credentials"})

        self.public_session =  self.oauth.get_session(token)


    # Get a list of songs with search in the name
    def get_songs(self, search, count):
        songs = []

        # We don't want white space of punctuation to confuse us when comparing song names.
        canonical_name = Spotify.canonical_name(search)

        # We have to get 50 songs at a time.
        skip = 0
        take = 50
        while len(songs) < count:
            tracks = self.public_session.get(
                'search',
                params={
                    'q': search,
                    'type': 'track',
                    'limit': take,
                    'offset': skip
                }).json()

            if not tracks:
                # There are not more songs to find.
                break

            # Search could find the search string in other places besides the name
            # so filter the songs returned
            songs.extend([
                {
                    'name': track['name'],
                    'artists': [ artist['name'] for artist in track['artists'] ],
                    'popularity': track['popularity'],
                    'id': Spotify.uri_to_id(track['uri'])
                }
                for track
                in tracks['tracks']['items']
                if canonical_name in Spotify.canonical_name(track['name'])
            ])

            skip += take

        # Its possible that the loop above could add a few too many songs.
        return songs[:count]


    # Get the authorized spotify user.
    def get_user(self):
        token = session.get('token')
        if not token:
            return None

        spotify_session = self.oauth.get_session(token)
        me = spotify_session.get('me').json()
        if 'error' in me:
            # TODO
            return None

        return { 'user_id': me['id'], 'session': spotify_session }


    # Make a playlist
    def make_playlist(self, user, name, song_ids):
        user_id = user['user_id']
        spotify_session = user['session']

        # If the a playlist with this name already exists then add these songs to that playlist.
        playlist_id = next(
            (
                playlist['id']
                for playlist 
                in self.get_playlists(user) 
                if playlist['name'] == name
            ),
            None)

        if playlist_id:
            # The playlist already exists. 
            # Remove any song already in the playlist
            existing_ids = [
                song['id']
                for song in 
                self.get_playlist(user, playlist_id)['songs']
            ]
            song_ids = (
                song_id 
                for song_id
                in song_ids
                if not song_id in existing_ids 
            )
        else:
            # Make the playlist
            playlist_json = spotify_session.post(
                f'users/{user_id}/playlists',
                json={
                    'name': name,
                    'description': 'Made with that1song.com',
                    'public': False
                }).json()
            playlist_id = Spotify.uri_to_id(playlist_json['uri'])

        spotify_session.post(
            f'playlists/{playlist_id}/tracks',
            json = { 'uris': ['spotify:track:' + id for id in song_ids] })

        return playlist_id


    # Get a user's playlist
    def get_playlist(self, user, playlist_id):
        playlist = user['session'].get(f'playlists/{playlist_id}').json()
        return {
            'name': playlist['name'],
            'songs': [
                { 'name': item['track']['name'], 'id': item['track']['id'] }
                for item
                in playlist['tracks']['items']
            ]
        }

    # Get a user's playlists
    def get_playlists(self, user):
        playlists = user['session'].get(f'me/playlists').json()
        return [
            {'id': playlist['id'], 'name': playlist['name']}
            for playlist
            in playlists['items']
        ]


    def get_authorize_url(self, callback_url):
        return self.oauth.get_authorize_url(
            scope = 'playlist-modify-private playlist-read-private',
            response_type = 'code',
            redirect_uri = callback_url)


    def authorize(self, code, callback_url):
        token = self.oauth.get_access_token(
            decoder = Spotify.utf8_json_decoder,
            data = {
                "code": code,
                "redirect_uri": callback_url,
                "grant_type": "authorization_code"
            }
        )
        session['token'] = token


    # We don't want white space of punctuation to confuse us when comparing song names.
    def canonical_name(name):
        name = name.lower()
        name = re.sub('[^a-z]+', ' ', name)
        return name.strip()


    def uri_to_id(uri):
        return uri.split(':')[2]


    def utf8_json_decoder(data):
        return json.loads(data.decode('utf-8'))