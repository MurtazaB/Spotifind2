from flask import Flask, request, redirect, g, render_template

import requests

import urllib
import base64

## For Bootstrap templates
# from flask_bootstrap import Bootstrap

app = Flask(__name__)

## Needed for Bootstrap
# Bootstrap(app)

# MAIN ID VARIABLES
clientID = '7193434ccce948f38b5eb4b929a06e60';
clientSecret = '8b0140d512724e84bdb3e3c121666431';

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


@app.route('/')
def home():
	return render_template('home.html', pageName='Home')

@app.route('/authenticate')
def authenticate():
	# TODO: change to render the right template
	return render_template('home.html', pageName='Home')

@app.route('/user/most-recent')
def mostRecentlyPlayed():
	return "Test";

@app.route('/discover')
def discover():
	return render_template('discover.html', pageName='Discover')