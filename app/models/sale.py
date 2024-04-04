from app.extensions import db

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Staff_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    Date = db.Column(db.Date, nullable=False)
    Tax = db.Column(db.Float, nullable=True)
    Discount = db.Column(db.Float, nullable=True)
    Type_Payment = db.Column(db.String, nullable=True) # EG: Cash, E-Wallet, Other
    No_Refer = db.Column(db.String, nullable=True) # EG: duitnow id
    Total = db.Column(db.Float, nullable=False)
    Status =  db.Column(db.String, nullable=False) # E.g: Paid, Daft
    Sale_items = db.relationship('Sale_Item',backref='sale',lazy=True)  # Improved loading
    def _repr_(self):
        return f'<SalesDetails "{self.id}...">'
    
class Sale_Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Report_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    Inventory_id = db.Column(db.Integer,db.ForeignKey('inventory.id'), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)
    SalePrice = db.Column(db.Float, nullable=False)