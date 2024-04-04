from app.dailySalesReport import bp
from app.models.dailysalesreport import DailySalesReport,Sale
from flask import render_template, request, redirect, url_for
from app import db

