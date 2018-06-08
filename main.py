import os
import logging
from authomatic import Authomatic
from authomatic.providers import oauth2, oauth1
from flask import Flask, render_template, send_from_directory

CONFIG = {
    'tw': {  # Your internal provider name
        'class_': oauth1.Twitter,
        # Twitter is an AuthorizationProvider so we need to set several other properties too:
        'consumer_key': '########################',
        'consumer_secret': '########################',
    },
    'fb': {
        'class_': oauth2.Facebook,
        # Facebook is an AuthorizationProvider too.
        'consumer_key': '204638593683246',
        'consumer_secret': '########################',
    }
}

app = Flask(__name__)
static = os.path.join(app.root_path, 'static')
pages = ('arrangements', 'biography', 'gallery', 'privacy', 'tributes')
authomatic = Authomatic(CONFIG, 'asKDkwdsawew92kDKlwkdw2030ODkdfw')

@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html', home=True)


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
