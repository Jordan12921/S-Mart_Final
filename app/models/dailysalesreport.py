from app import db

#class DB
class DailySalesReport(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    Staff_id = db.Column(db.String, db.ForeignKey('staff.id'), nullable=False)
    Date = db.Column(db.Date, nullable=False)

    Sales = db.relationship('Sale',backref='daily_sales_report', lazy=True)  # Improved loading
    

    def _repr_(self):
        return f'<SalesReport "{self.id}">'
    

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Report_id = db.Column(db.Integer, db.ForeignKey('daily_sales_report.id'), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)
    SalePrice = db.Column(db.Float, nullable=False)
    Subtotal = db.Column(db.Float, nullable=False)

    Inventory_id = db.Column(db.Integer,db.ForeignKey('inventory.id'), nullable=False)


    def _repr_(self):
        return f'<SalesDetails "{self.id}...">'