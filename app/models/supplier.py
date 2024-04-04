from app import db


class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String, nullable=False)
    Contact = db.Column(db.String, nullable=True)
    Address = db.Column(db.String, nullable=True)
    Comment = db.Column(db.String, nullable=True)
    # Products = db.relationship('Product', backref='supplier', lazy=True)

