from functools import wraps
import enum
import json
import os
from os import environ as env
from werkzeug.exceptions import HTTPException
import logging
from dotenv import load_dotenv, find_dotenv
from flask import (Flask, jsonify, redirect, render_template,
                   request, send_from_directory, session, url_for)
from flask_sqlalchemy import SQLAlchemy
from authlib.flask.client import OAuth
from six.moves.urllib.parse import urlencode
import requests

from dotenv import load_dotenv, find_dotenv
import constants

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

AUTH0_CALLBACK_URL = env.get(constants.AUTH0_CALLBACK_URL)
AUTH0_CLIENT_ID = env.get(constants.AUTH0_CLIENT_ID)
AUTH0_CLIENT_SECRET = env.get(constants.AUTH0_CLIENT_SECRET)
AUTH0_DOMAIN = env.get(constants.AUTH0_DOMAIN)
AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
AUTH0_AUDIENCE = env.get(constants.AUTH0_AUDIENCE)
if AUTH0_AUDIENCE is '':
    AUTH0_AUDIENCE = AUTH0_BASE_URL + '/userinfo'
DATABASE_URI = env.get(constants.DATABASE_URI)

app = Flask(__name__)
app.secret_key = constants.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Tributes(enum.Enum):
    candle = 1
    flower = 2
    tribute = 3


class Tribute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Unicode(80))
    name = db.Column(db.Unicode(80))
    kind = db.Column(db.Enum(Tributes))
    text = db.Column(db.UnicodeText)

    def __init__(self, user, name, kind, text):
        self.user = user
        self.name = name
        self.kind = kind
        self.text = text

    def __repr__(self):
        return '<Tribute %r>' % self.user


static = os.path.join(app.root_path, 'static')
pages = ('arrangements', 'biography', 'gallery', 'privacy', 'tributes')

oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    api_base_url=AUTH0_BASE_URL,
    access_token_url=AUTH0_BASE_URL + '/oauth/token',
    authorize_url=AUTH0_BASE_URL + '/authorize',
    client_kwargs={
        'scope': 'openid profile',
    },
)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if constants.PROFILE_KEY not in session:
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated


@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html', home=True)


@app.route('/auth')
def callback_handling():
    resp = auth0.authorize_access_token()

    url = AUTH0_BASE_URL + '/userinfo'
    headers = {'authorization': 'Bearer ' + resp['access_token']}
    resp = requests.get(url, headers=headers)
    userinfo = resp.json()

    session[constants.JWT_PAYLOAD] = userinfo

    session[constants.PROFILE_KEY] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture']
    }
    logging.info(userinfo)

    return redirect(url_for('dashboard'))


@app.route('/login')
@app.route('/login.html')
def login():
    return auth0.authorize_redirect(
        redirect_uri=AUTH0_CALLBACK_URL, audience=AUTH0_AUDIENCE)


@app.route('/logout')
@app.route('/logout.html')
def logout():
    session.clear()
    params = {
        'returnTo': url_for('index', _external=True),
        'client_id': AUTH0_CLIENT_ID
    }
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


@app.route('/dashboard.html')
@requires_auth
def dashboard():
    return render_template('dashboard.html',
                           userinfo=session[constants.PROFILE_KEY])


@app.route('/tribute/<kind>', methods=['GET', 'POST'])
@requires_auth
def write_tribute(kind):
    if request.form:
        user = session[constants.PROFILE_KEY]['user_id']
        name = session[constants.PROFILE_KEY]['name']
        text = request.form.get('text')
        tribute = Tribute(kind=kind, text=text, user=user, name=name)
        db.session.add(tribute)
        db.session.commit()
        return redirect(url_for('tributes'))

    return render_template('tribute.html',
                           kind=kind, userinfo=session[constants.PROFILE_KEY])


@app.route('/tributes.html')
def tributes():
    tributes = Tribute.query.all()
    return render_template('tributes.html', tributes=tributes)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        static, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/pages/<page>.html')
def sign(page):
    if page in pages:
        return render_template('%s.html' % page)
    return render_template('404.html')


@app.errorhandler(404)
def handle_404(error):
    logging.info(error)
    return render_template('404.html')


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(500)
def handle_error():
    return render_template('error.html')


@app.errorhandler(Exception)
def handle_auth_error(ex):
    response = jsonify(message=str(ex))
    response.status_code = (ex.code if isinstance(ex, HTTPException) else 500)
    return response
