from flask import Flask

application = Flask(__name__)


@application.route('/')
def index():
  return 'Welcome'


if __name__ == '__main__':
  application.run(port=9876, debug=True)

