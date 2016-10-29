from flask import Flask, request, redirect, g, render_template, session
import flask
import requests
import json
import urllib
import base64

## For Bootstrap templates
# from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.secret_key = 'superSecret'




## Needed for Bootstrap
# Bootstrap(app)

# MAIN ID VARIABLES
CLIENT_ID = '7193434ccce948f38b5eb4b929a06e60';
CLIENT_SECRET = '8b0140d512724e84bdb3e3c121666431';

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 5000
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private user-top-read streaming user-library-modify user-library-read"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()


auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

@app.route('/')
def home():
    print('api_session_token' in session)
    return render_template('home.html', pageName='Home')

@app.route('/authenticate')
def authenticate():
	url_args = "&".join(["{}={}".format(key,urllib.quote(val)) for key,val in auth_query_parameters.iteritems()])
	auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
	return redirect(auth_url)

@app.route("/getFavorites")
def getFavorites():
    fav_url = "https://api.spotify/v1/me/top/tracks?limit=10"
    if "api_session_token" not in flask.session:
        return "Session not found"
    fav_response = requests.get(fav_url)#, headers=headers)
    response_data = json.loads(fav_response.text);

    result = []

    for i in response_data:
        result.append(i['id'])

    return result;

@app.route('/discover')
def discover():
	return render_template('discover.html', pageName='Discover')

@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
    base64encoded = base64.b64encode("{}:{}".format(CLIENT_ID, CLIENT_SECRET))
    headers = {"Authorization": "Basic {}".format(base64encoded)}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]
    session.modified = True;

    session['api_session_token'] = access_token
    session.modified = True;
    print session['api_session_token'];

    print 'Session token ' + session['api_session_token'];
    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization":"Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # Get user playlist data
    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)

    # Combine profile and playlist data to display
    display_arr = [profile_data] + playlist_data["items"];
    return render_template("index.html",sorted_array=display_arr)
