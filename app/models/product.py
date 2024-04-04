from app import db
from datetime import datetime, timedelta
from sqlalchemy.ext.hybrid import hybrid_property

# Product model
product_category = db.Table('product_category',
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

class Product(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    BarCode = db.Column(db.String,nullable=False)
    Name = db.Column(db.String, nullable=False)
    Safety_quantity = db.Column(db.Integer,nullable=False)
    Status = db.Column(db.String, nullable=False) # "NotAvailable","OutOfStock","InStock"
    Inventories = db.relationship('Inventory',backref='product',lazy=True)  # Improved loading
    Categories = db.relationship('Category',secondary=product_category, backref=db.backref('products', lazy=True), lazy='subquery')
    
    
    def _repr_(self):
        return f'<Product "{self.Name}">'
    
    def delete(self):
        # Delete associated inventory items
        for inventory in self.Inventories:
            inventory.delete()
        # Delete the product itself
        db.session.delete(self)
        db.session.commit()
    
class Inventory(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    Product_id = db.Column(db.Integer,db.ForeignKey('product.id'),nullable=False)
    Supplier_id = db.Column(db.Integer,db.ForeignKey('supplier.id'),nullable=False)
    StockInDate = db.Column(db.Date, nullable=False)
    ExpiryDate = db.Column(db.Date, nullable=False)
    Init_QTY = db.Column(db.Integer, nullable=True)
    Available_QTY = db.Column(db.Integer, nullable=False)
    Locked_QTY = db.Column(db.Integer, nullable=False)
    Lost_QTY = db.Column(db.Integer, nullable=False)
    Sold_QTY = db.Column(db.Integer, nullable=False)
    CostPerItem = db.Column(db.Double, nullable=False)
    RetailPrice = db.Column(db.Double,nullable=False)

    def delete(self):
        # Perform any additional cleanup actions if needed
        # Delete the inventory item
        db.session.delete(self)
        db.session.commit()


    def _repr_(self):
        return f'<Stock "{self.StockInDate}...">'
    
    @hybrid_property
    def days_to_expiry(self):
        return (self.ExpiryDate - datetime.utcnow().date()).days
    
    @staticmethod
    def get_nearing_expiry_items():
        today = datetime.utcnow().date()  
        thirty_days_ahead = today + timedelta(days=30)
        nearing_expiry_items = Inventory.query.filter(Inventory.ExpiryDate > today, Inventory.ExpiryDate <= thirty_days_ahead).all()
        return nearing_expiry_items
    

class LostReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    particulars = db.Column(db.String(255)) 
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    qty_lost = db.Column(db.Integer, nullable=False)
    remark = db.Column(db.String(255), nullable=False)