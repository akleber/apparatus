from flask import Flask
from flask_qrcode import QRcode

app = Flask(__name__)

# https://marcoagner.github.io/Flask-QRcode/
qrcode = QRcode(app)

from app import routes
