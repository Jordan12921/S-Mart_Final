from flask import Flask, Blueprint
bp = Blueprint('sale',__name__)


from app.sale import sale_routers