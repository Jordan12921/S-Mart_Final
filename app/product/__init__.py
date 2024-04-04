from flask import Flask, Blueprint
bp = Blueprint('product',__name__)


from app.product import product_routers,inventory_routers,loss_routers