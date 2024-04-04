from datetime import date, datetime
from flask_login import login_required
import sqlalchemy
from app.cashflow.routes import insert_to_cashflow
from app.models.supplier import Supplier
from app.product import bp
from flask import flash, render_template, request, redirect, url_for
from app.models.product import LostReport, Product,Inventory
from app import db
import time

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, IntegerField, DateField, DecimalField
from wtforms.validators import InputRequired, NumberRange, DataRequired
from flask_principal import Permission,RoleNeed
admin_permission = Permission(RoleNeed('admin'))
class InventoryForm(FlaskForm):
    product_id = IntegerField('Product ID', validators=[InputRequired()])
    supplier = SelectField('Supplier', choices=[],validators=[DataRequired()])
    stock_in_date = DateField('Stock In Date', validators=[InputRequired()])
    expiry_date = DateField('Expiry Date', validators=[InputRequired()])
    init_qty = IntegerField('Initial Quantity', validators=[InputRequired(),NumberRange(min=0)])
    cost_per_item = DecimalField('Cost Per Item', validators=[InputRequired(), NumberRange(min=0)])
    retail_price = DecimalField('Retail Price', validators=[InputRequired(), NumberRange(min=0)])

@bp.route('/inventory/<int:id>', methods=['GET'])
def inventory_detail(id):
    if not id:
        id = request.args.get('inventory',None,int)

    inventory = Inventory.query.filter(Inventory.id == id).first()
    lost_reports = LostReport.query.filter(LostReport.inventory_id == id).all()
    suppliers = Supplier.query.all()
    return render_template('/product/inventory_detail.html',inventory = inventory,suppliers=suppliers,lost_reports = lost_reports)

@bp.route('/<barcode>/inventory/create', methods=['POST'])
@login_required
@admin_permission.require(http_exception=401)
def add_inventory(barcode):

    form = InventoryForm()
    print(form.product_id.data)
    print(form.validate())
    if request.method=="POST" and barcode:
        product = db.one_or_404(db.select(Product).filter_by(BarCode=barcode))
        # storein_date = datetime.strptime(request.form['storein_date'], '%Y-%m-%d')
        # expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d')
        # supplier = Supplier.query.filter(Supplier.Name == request.form['supplier']).first()
        # quantity =int(request.form['quantity'])
        # costprice = float(request.form['cost_per_item'])
        # retailprice =float( request.form['retail_price'])

        new_inventory =  Inventory(
            product = product,
            Supplier_id =   form.supplier.data,
            StockInDate =   form.stock_in_date.data,
            ExpiryDate  =   form.expiry_date.data,
            Init_QTY    =   form.init_qty.data,
            Available_QTY=  form.init_qty.data,
            Locked_QTY  =   0,
            Lost_QTY    =   0,
            Sold_QTY    =   0,
            CostPerItem =   form.cost_per_item.data,
            RetailPrice =   form.retail_price.data
        )

        try:
            db.session.add(new_inventory)
            db.session.commit()
            insert_to_cashflow(
                particular=f'Stock in - <{product.Name}>',
                debit=0.00,
                credit=float(form.init_qty.data * form.cost_per_item.data)
            )
        except Exception as e:
            db.session.rollback()
            return f"error: {str(e)}",500
        
    return redirect(url_for("product.get_product",id=product.id))


@bp.route('/inventory/delete/<int:id>', methods=['GET'])
@login_required
@admin_permission.require(http_exception=401)
def delete_inventory(id):
    if not id:
        id = request.args.get('id',None,int)
    print('ysss')
    inventory = Inventory.query.get_or_404(id)

    if inventory:
        product_id = inventory.Product_id
        try:
            db.session.delete(inventory)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
        return redirect(url_for('product.get_product',id = product_id))
    
    return redirect(url_for('product.index'))


@bp.route('/inventory/edit/<int:id>', methods=['POST'])
@login_required
def edit_inventory(id):
    if not id:
        id = request.args.get('id',None,int)
    inventory = Inventory.query.get_or_404(id)
    if not inventory:
        return "Inventory not found, 404"

    inventory.Supplier_id = request.form['supplier']
    inventory.StockInDate = datetime.strptime(request.form['new_stockin'],'%Y-%m-%d').date()
    inventory.ExpiryDate = datetime.strptime(request.form['new_expiry'],'%Y-%m-%d').date()
    inventory.CostPerItem = float(request.form['costperitem'])
    inventory.Init_QTY = request.form['init_qty']
    inventory.Available_QTY = request.form['available_qty']
    inventory.Locked_QTY = request.form['locked_qty']
    inventory.Sold_QTY = request.form['sold_qty']
    inventory.Lost_QTY = request.form['lost_qty']
    inventory.RetailPrice = float(request.form['retailprice'])

    db.session.commit()

    return redirect(url_for("product.get_product",id = inventory.Product_id))


# product/inventory_routers.py
def insert_data_to_invenory(df):
    try:
        for index, row in df.iterrows():
            time.sleep(0.5)
            # Get or create Product based on name
            product_name = row['Product']
            product = Product.query.filter_by(Name=product_name).first()
            if not product or product is None:
                # Create a new Product if not found
                product = Product(BarCode = row['BarCode'],Name=product_name,Safety_quantity = -1,Status="InStock")
                db.session.add(product)
                db.session.commit()
            
            # Get or create Supplier based on name
            supplier_name = row['Supplier']
            supplier = Supplier.query.filter_by(Name=supplier_name).first()
            if not supplier or supplier is None:
                # Create a new Supplier if not found
                supplier = Supplier(Name=supplier_name)
                db.session.add(supplier)
                db.session.commit()
            
            
            stockInDate=row['StockInDate']
            expiryDate=row['ExpiryDate']
            if isinstance(stockInDate, date):
                stockInDate=datetime.strftime(row['StockInDate'], '%Y-%m-%d')
                expiryDate=datetime.strftime(row['ExpiryDate'], '%Y-%m-%d')
            
            stockInDate=datetime.strptime(stockInDate, '%Y-%m-%d').date()
            expiryDate=datetime.strptime(expiryDate, '%Y-%m-%d').date()
            print(stockInDate)
            # Create Inventory item
            inventory = Inventory.query.filter(Inventory.Product_id == product.id,Inventory.Init_QTY == row["Init_QTY"],Inventory.CostPerItem==row["CostPerItem"], Inventory.StockInDate == stockInDate,Inventory.ExpiryDate == expiryDate).first()
            if inventory:
                continue
            
            inventory = Inventory(
                Product_id=product.id,
                Supplier_id = supplier.id,
                # StockInDate=date(stockInDate.year,stockInDate.month,stockInDate.day),
                # ExpiryDate=date(expiryDate.year,expiryDate.month,expiryDate.day),
                StockInDate=stockInDate,
                ExpiryDate=expiryDate,
                Init_QTY=row['Init_QTY'],
                Available_QTY=row['Available_QTY'],
                Locked_QTY=row['Locked_QTY'],
                Lost_QTY=row['Lost_QTY'],
                Sold_QTY=row['Sold_QTY'],
                CostPerItem=row['CostPerItem'],
                RetailPrice=row['RetailPrice']
            )
            db.session.add(inventory)
            db.session.commit()
            time.sleep(0.4)
            insert_to_cashflow(particular=f'StockIn {product_name}',debit=0.00,credit=(float(row['Init_QTY']) * float(row['CostPerItem'])),remark=f'StockIn Date: {stockInDate}')
            
        
        return True, None  # Success
    except Exception as e:
        db.session.rollback()
        return False, str(e) 