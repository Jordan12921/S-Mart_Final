from flask import Flask, Blueprint
bp = Blueprint('supplier',__name__)


from app.supplier import routes