from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Procurement, Item
from app import db

bid_routes_bp = Blueprint('bid_routes', __name__, url_prefix='/bids')

@bid_routes_bp.route('/')
def list_bids():
    procurements = Procurement.query.filter(Procurement.status != 'Archived').order_by(Procurement.created_at.desc()).all()
    return render_template('bids/list.html', procurements=procurements)
