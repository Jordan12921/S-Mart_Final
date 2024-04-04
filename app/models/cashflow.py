from app.extensions import db

class Cashflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    particulars = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    debit = db.Column(db.Float, default=0)
    credit = db.Column(db.Float, default=0)
    balance = db.Column(db.Float, default=0)
    remarks = db.Column(db.String(255))

    def __repr__(self):
        return f"Cashflow('{self.particulars}', '{self.date}', '{self.debit}', '{self.credit}', '{self.balance}', '{self.remarks}')"
