import os
import logging
from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)
static = os.path.join(app.root_path, 'static')
pages = ('arrangements', 'biography', 'gallery', 'tributes')

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
