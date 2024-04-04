from flask import Flask, Blueprint
bp = Blueprint('category',__name__)


from app.category import routes