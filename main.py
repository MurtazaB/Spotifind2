from flask import Flask, request, redirect, g, render_template, session
import flask
import requests
import json
import urllib
import base64
import pprint
import html2text

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
    createPlaylistIfNeeded();
    print('api_session_token' in session)
    return render_template('home.html', pageName='Home')

@app.route('/authenticate')
def authenticate():
	url_args = "&".join(["{}={}".format(key,urllib.quote(val)) for key,val in auth_query_parameters.iteritems()])
	auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
	return redirect(auth_url)


# @app.route('/discover')
# def discover():
# 	# Set discoverList to provide the right information
# 	discoverList = [1, 2, 3, 4, 5]
# 	return render_template('discover.html', pageName='Discover', discoverList=discoverList)


def getFavorites():
    fav_url = "https://api.spotify.com/v1/me/top/tracks?limit=5"
    if "api_session_token" not in flask.session:
        return "Session not found"
    authorization_header = {"Authorization":"Bearer {}".format(session["api_session_token"])}
    fav_response = requests.get(fav_url, headers=authorization_header)
    response_data = json.loads(fav_response.text)['items'];
    #print pprint.PrettyPrinter(depth=6).pprint(response_data)

    result = []

    for i in response_data:
        result.append(i['id'])

    return result

def playlistExists():
    if "api_session_token" not in flask.session:
        return False

    query_url = "https://api.spotify.com/v1/me/playlists"
    authorization_header = {"Authorization":"Bearer {}".format(session["api_session_token"])}
    response = requests.get(query_url, headers=authorization_header)
    response_data = json.loads(response.text)['items']


    for item in response_data:
        if item['name'] == 'Spotifind':
            session['playlist_id'] = item['id']
            print 'playlist id ' + session['playlist_id']
            return True
    return False

def createPlaylistIfNeeded():
    if playlistExists():
        return

    if 'api_username' not in flask.session:
        return
    payload = {'name' : 'Spotifind'}
    query_url = "https://api.spotify.com/v1/users/{}/playlists".format(session['api_username'])
    query_url = query_url + '?name=Spotifind'
    authorization_header = {"Authorization":"Bearer {}".format(session["api_session_token"])}

    response = requests.post(query_url, data=json.dumps(payload),headers=authorization_header)
    response_data = json.loads(response.text)
    session['playlist_id'] = response_data['id']

    print 'playlist created: ' + session['playlist_id']



@app.route('/match')
def match():
    library_url = 'https://api.spotify.com/v1/users/12127542408/playlists/1GBIt73qNiPXpj5ypOEI4d/tracks'

    if "api_session_token" not in session:
        return redirect("127.0.0.1:5000")

    favorites = getFavorites();


    favoriteQuery = ','.join(favorites)

    query_url = "https://api.spotify.com/v1/audio-features"
    authorization_header = {"Authorization":"Bearer {}".format(session['api_session_token'])}
    appended_url = query_url + '?ids=' + favoriteQuery
    favorite_response = requests.get(appended_url, headers=authorization_header);
    response_data = json.loads(favorite_response.text)['audio_features'];


    library_response = requests.get(library_url, headers=authorization_header)
    library_response_data = json.loads(library_response.text)['items'];

    listed_library_ids = [];
    for thisItem in library_response_data:
        listed_library_ids.append(thisItem['track']['id'])

    libraryQualityUrl = query_url + "?ids=" + ",".join(listed_library_ids);
    library_response = requests.get(libraryQualityUrl, headers=authorization_header)
    library_quality_data = json.loads(library_response.text)['audio_features']

    mappedMatches = {}

    keys = ['danceability', 'energy', 'loudness', 'mode', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']

    for item in response_data:

        thisId = item['id'];


        bestId = -1;
        bestTotal = 100000

        secondBestId = -1;
        secondBestTotal = 100000

        for playlistSong in library_quality_data:


            total = 0
            difference = 0


            for key in keys:
                difference = abs(item[key] - playlistSong[key])
                total += difference

            if (difference < bestTotal):
                secondBestId = bestId
                secondBestTotal = bestTotal

                bestId = playlistSong['id']
                bestTotal = difference

        finalResponse = requests.get("https://api.spotify.com/v1/tracks?ids=" + bestId+","+secondBestId, headers=authorization_header);
        responseResult = json.loads(finalResponse.text)['tracks'];
        track = responseResult[0];

        bestTrack = {
        "title":track["name"],
        "artist":track["artists"][0]["name"],
        "id":track["id"],
        "picture":track["album"]["images"][1]["url"], #gives image URL
        "album":track["album"]["name"],
        "preview_url":track["preview_url"],
        "uri":track["uri"]
        }

        track = responseResult[1];
        secondTrack = {
        "title":track["name"],
        "artist":track["artists"][0]["name"],
        "id":track["id"],
        "picture":track["album"]["images"][1]["url"], #gives image URL
        "album":track["album"]["name"],
        "preview_url":track["preview_url"],
        "uri":track["uri"]
        }

        mappedMatches[thisId] = [bestTrack, secondTrack]

    output_list = []
    for key in mappedMatches:
        originalInfo = requests.get("https://api.spotify.com/v1/tracks/" + key, headers=authorization_header);
        responseResult = json.loads(originalInfo.text);
        name = responseResult['name'] + ' by ' + responseResult['album']['artists'][0]['name']
        for value in mappedMatches[key]:
            value['matched_item'] = name
            output_list.append(value)

    #calling getBlurb() and passing it out with render_template
    only_songnames_list = getTopTenSongnames(output_list)
    blurb_dict = getBlurb(only_songnames_list)

    output_list = sorted(output_list, key=lambda b: b['id'])
    print pprint.PrettyPrinter(depth=6).pprint(output_list)
    return render_template('discover.html', pageName='Discover',discoverList=output_list, blurb_dict=blurb_dict)


@app.route('/discover')
def discover():
    favorites = getFavorites()
    fav_str = ','.join(favorites)
    print fav_str

    disc_url = "https://api.spotify.com/v1/recommendations?limit=10&seed_tracks={}".format(fav_str)
    if "api_session_token" not in session:
        return redirect("127.0.0.1:5000/")
    authorization_header = {"Authorization":"Bearer {}".format(session['api_session_token'])}
    disc_response = requests.get(disc_url, headers=authorization_header)
    response_data = json.loads(disc_response.text);

    output_list = []
    for track in response_data["tracks"]:
        track_dict = {
        "title":track["name"],
        "artist":track["artists"][0]["name"],
        "id":track["id"],
        "picture":track["album"]["images"][1]["url"], #gives image URL
        "album":track["album"]["name"],
        "preview_url":track["preview_url"],
        "uri":track["uri"]
        }
        #print track_dict
        output_list.append(track_dict)
    print pprint.PrettyPrinter(depth=6).pprint(output_list)
    return render_template('discover.html', pageName='Discover',discoverList=output_list)

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
    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization":"Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    session['api_username'] = profile_data['id']
    # Get user playlist data
    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)

    # Combine profile and playlist data to display=
    display_arr = [profile_data] + playlist_data["items"];
    return redirect('http://127.0.0.1:5000/')

def getTopTenSongnames(match_output_dict):
    output_list = []
    for track_dict in match_output_dict:
        #print track_dict["title"]
        output_list.append(track_dict["title"])
    return output_list

def getBlurb(songname_list):
    input_list = songname_list
    wiki_urls = []
    for song in input_list:
        song = urllib.quote(song.encode('utf8'))
        wiki_api_url = "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&generator=allpages&gaplimit=1&gapfilterredir=nonredirects&gapfrom={}&format=json".format(song)
        #print wiki_api_url
        wiki_urls.append(wiki_api_url)

    output_dict = {}
    h = html2text.HTML2Text()
    song_index = 0
    for page in wiki_urls:
        r = requests.get(page)
        r1 = json.loads(r.text)
        for key_pagenum in r1['query']['pages'].keys():
            rawtext = r1['query']['pages'][key_pagenum]['extract']
        blurb = h.handle(rawtext)
        output_dict[input_list[song_index]] = (blurb)
        song_index+=1

    print(output_dict)
    return output_dict
