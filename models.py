from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    client = db.Column(db.String(50), nullable=False)
    item = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    supply_price = db.Column(db.Integer, nullable=False)
    tax = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)