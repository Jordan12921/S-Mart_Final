# from app.extensions import db

# #class Stock DB
# class Inventory(db.Model):
#     id = db.Column(db.Integer, nullable=False, primary_key=True)
#     BarCode = db.Column(db.String, nullable=False)
#     StockName = db.Column(db.String, nullable=False)
#     Category = db.Column(db.String, nullable=False)
#     StockInDate = db.Column(db.Date, nullable=False)
#     ExpiryDate = db.Column(db.Date, nullable=False)
#     Quantity = db.Column(db.Integer, nullable=True)
#     CostPricePerItem = db.Column(db.Double, nullable=False)
#     RetailPrice = db.Column(db.Double, nullable=False)

#     def __init__(self,BarCode,StockName,Category,StockInDate,ExpiryDate,Quantity,CostPricePerItem,RetailPrice):
#         self.BarCode = BarCode
#         self.StockName = StockName
#         self.Category = Category
#         self.StockInDate = StockInDate
#         self.ExpiryDate = ExpiryDate
#         self.Quantity = Quantity
#         self.CostPricePerItem = CostPricePerItem
#         self.RetailPrice = RetailPrice

#     def _repr_(self):
#         return f'<Stock "{self.Inventory}">'