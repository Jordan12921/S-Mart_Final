from flask import Flask, Blueprint
bp = Blueprint('user',__name__)


from app.user import routes