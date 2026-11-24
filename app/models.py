from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Procurement(db.Model):
    __tablename__ = 'procurement'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    abc = db.Column(db.String(100))
    pre_bid_date = db.Column(db.String(100))
    place_of_bidding = db.Column(db.String(255))
    municipality = db.Column(db.String(100))
    agency = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(20), default='Ongoing')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('Item', backref='procurement', lazy=True)


class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    procurement_id = db.Column(db.Integer, db.ForeignKey('procurement.id', ondelete='SET NULL'), nullable=True)
    code = db.Column(db.String(50))
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))
    price = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(50))
    target_qty = db.Column(db.Integer, default=1)
    current_qty = db.Column(db.Integer, default=0)
    expiration_date = db.Column(db.Date, nullable=True)
    delivery_checked = db.Column(db.Boolean, default=False, nullable=False)


class AvailableStock(db.Model):
    __tablename__ = 'available_stock'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    unit = db.Column(db.String(50))
    expiration_date = db.Column(db.Date, nullable=True)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320), nullable=True)
    reset_token_hash = db.Column(db.String(64), nullable=True)
    reset_token_expires_at = db.Column(db.BigInteger, nullable=True)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
