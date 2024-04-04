from flask import Flask, Blueprint
bp = Blueprint('dailysalesreport',__name__)


from app.dailySalesReport import report_routes, salesDetails_routes