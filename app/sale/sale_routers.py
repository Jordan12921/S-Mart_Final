from datetime import datetime,date, timedelta
from flask_login import current_user, login_required
from app.cashflow.routes import insert_to_cashflow
from app.models.product import Product,Inventory
from app.models.user import User
from app.sale import bp
from app.models.sale import Sale, Sale_Item
from flask import render_template, request, redirect, url_for
from app import db, update_qty_on_expiry
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, DecimalField, BooleanField, SubmitField
from wtforms.validators import InputRequired, NumberRange

class PaymentForm(FlaskForm):
    type_payment = StringField('Type Payment', validators=[InputRequired()], render_kw={"autocomplete": "off"})
    no_refer = StringField('No. Refer', validators=[], render_kw={"autocomplete": "off"})
    discount = DecimalField('Discount (%)', validators=[InputRequired(), NumberRange(min=0)], places=2)
    total = DecimalField('Total', validators=[InputRequired(), NumberRange(min=0)], places=2)
    custom_price = BooleanField('Save Custom Total Price')
    submit = SubmitField('End Payment')

    choices = [('cash', 'Cash'), ('e-wallet/DuitNow', 'E-Wallet/DuitNow')]
    type_payment = SelectField('Select an option', choices=choices,default='cash')

@bp.route('/', methods=['GET','POST'])
@login_required
def sales_index():
    update_qty_on_expiry()
    sales, product_totals,staff_totals = get_Info()
    total_sales =  db.session.query(db.func.sum(Sale.Total)).filter(Sale.Status=='paid').scalar()  

    return render_template('sales/index.html',sales = sales,products = product_totals,staff_totals = staff_totals,date = date,total_sales=total_sales)

def get_Info():
    sales = db.session.query(Sale.Date,Sale.Discount,Sale.Type_Payment,db.func.sum(Sale.Total).label('Total'),Sale.Status).filter(Sale.Status=="paid").group_by(Sale.Date,Sale.Discount,Sale.Type_Payment).all()
    product_query_totals = db.session.query(Product.Name,db.func.sum(Sale_Item.Quantity).label("Quantity")).filter(Sale.Date == date.today(),Sale.id == Sale_Item.Report_id,Sale.Status == "paid",Inventory.Product_id == Product.id,Inventory.id == Sale_Item.Inventory_id).group_by(Product.Name).all()
    # today_records = Sale.query.filter(Sale.Date == date.today()).all()
    staff_query_totals = db.session.query(Sale.Staff_id,(User.Last_Name + ' ' + User.First_Name).label('Name'),db.func.sum(Sale.Total).label("Total_Amount"))\
                            .filter(Sale.Date == date.today(),User.id == Sale.Staff_id)\
                            .group_by(Sale.Staff_id)\
                            .all()

    return sales, product_query_totals, staff_query_totals

@bp.route('/search')
@login_required
def search_sales():
    sales, product_totals,staff_totals = get_Info()

    start_date = request.args.get('start_date')
    end_date =request.args.get('end_date')

    print(f"start date: {start_date}, enddate: {end_date}")
    # Convert string inputs to datetime objects
    # start_date = datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=1)
    # end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    start_date = datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=1)
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    
    # Query database for records within the specified date range
    # sales = Sale.query.filter(Sale.Date>=start_date,Sale.Date<=end_date).all()
    sales =  db.session.query(Sale.Date,Sale.Discount,Sale.Type_Payment,db.func.sum(Sale.Total).label('Total'),Sale.Status).filter(Sale.Status=="paid",Sale.Date>=start_date,Sale.Date<=end_date).group_by(Sale.Date,Sale.Discount).all()
    total_sales =  db.session.query(db.func.sum(Sale.Total)).filter(Sale.Date>=start_date,Sale.Date<=end_date, Sale.Status=="paid").scalar()  
    return render_template('sales/index.html',sales = sales,products = product_totals,staff_totals = staff_totals,date = date,total_sales=total_sales)




def create_sale():
    sale = Sale(
        Staff_id=current_user.id, 
        Date = datetime.today(), 
        Tax = 0,
        Discount = 0, 
        Type_Payment = "", 
        No_Refer = "", 
        Total = 0, 
        Status ="draft"
        )
    try:
        db.session.add(sale)
        db.session.commit()
        return sale
    except Exception as e:
        db.session.rollback()
        return None

def get_draft_sale():
    return Sale.query.filter(Sale.Status == "draft").first()

@bp.route('/checkout/', methods=['GET','POST'])

@login_required
def show_checkout_page():
    products = Product.query.filter(Product.Status == "InStock").all()
    sale = get_draft_sale()
    form = PaymentForm()
    if sale:
        user = User.query.filter(User.id == current_user.id).first()
        sale.Staff_id = current_user.id
        sale.Date = datetime.today()
        update_sale_Total(sale.id)
        db.session.commit()

        # total_inventory = [sum(inventory.Available_QTY for inventory in product.Inventories) for product in products]
    else:
        sale = create_sale()
    return render_template('sales/checkout.html',products=products,sale = sale, form=form,username=current_user.Last_Name + '' + current_user.First_Name)



@bp.route('/add',methods=["GET"])
@login_required
def add_sale_item():
    item_id = request.args.get("item",None)
    if item_id:
        inventory = Inventory.query.filter(Inventory.Product_id == item_id, Inventory.Available_QTY > 0)\
                                   .order_by(Inventory.StockInDate).first()
        if inventory:

            sale = get_draft_sale()
            sale_item = Sale_Item.query.filter(Sale_Item.Inventory_id == inventory.id,Sale_Item.Report_id==sale.id).first()

            if sale_item:
                sale_item.Quantity += 1
            else:
                sale_item = Sale_Item(
                    sale = sale,
                    Inventory_id = inventory.id,
                    Quantity = 1,
                    SalePrice = inventory.RetailPrice
                )
                db.session.add(sale_item)
            inventory.Available_QTY -= 1
            inventory.Locked_QTY +=1
        db.session.commit()

    return redirect(url_for('sale.show_checkout_page'))


@bp.route('/<int:item>/delete',methods=["GET","POST"])
@login_required
def remove_sale_item_from_checkout(item):
    sale_item = Sale_Item.query.get_or_404(item)
    if sale_item.Quantity > 1:
        sale_item.Quantity -= 1
    else:
        db.session.delete(sale_item)
        db.session.commit()
    inventory = Inventory.query.get_or_404(sale_item.Inventory_id)
    inventory.Available_QTY += 1
    inventory.Locked_QTY -= 1
    db.session.commit()

    update_sale_Total(sale_item.Report_id)
    return redirect(url_for('sale.show_checkout_page')) 

@bp.route('/sale/<int:item>/delete',methods=["GET","POST"])
@login_required
def remove_sale_items(item):
    sale_item = Sale_Item.query.get_or_404(item)
    sale = Sale.query.get_or_404(sale_item.Report_id)
    inventory = Inventory.query.filter(Inventory.id == sale_item.Inventory_id).first()
    count_sale_items = Sale_Item.query.filter(Sale_Item.Report_id == sale.id).count()
    if inventory:
        inventory.Available_QTY += sale_item.Quantity
        inventory.Sold_QTY = 0

    db.session.delete(sale_item)
    db.session.commit()
    print("count: ",count_sale_items)
    if count_sale_items <= 1:
        db.session.delete(sale)
        db.session.commit()

    return render_template('sales/saledetail.html',sale=sale)
    

@bp.route('/<int:id>/checkout',methods=["GET","POST"])
@login_required
def finalize_checkout(id):
    sale =  Sale.query.get_or_404(id)
    form = PaymentForm()
    update_sale_Total(sale.id)
    if form.validate_on_submit():
        discount = float(form.discount.data)
        no_refer = form.no_refer.data
        type_payment = form.type_payment.data
        # if "custom_price" in request.form and request.form["custom_price"] == "True":
        if form.custom_price.data:
            total = float(form.total.data)
        else:  
            total = (sale.Total) - (sale.Total * (discount/100))

        sale.Date = datetime.today()
        sale.Discount = discount
        sale.No_Refer = no_refer
        sale.Type_Payment = type_payment
        sale.Total = "%.2f" % total
        sale.Status = "paid"
        db.session.commit()
    sale_items = Sale_Item.query.filter(Sale_Item.Report_id == sale.id).all()
    
    for sale_item in sale_items:
        inventory = Inventory.query.filter(Inventory.id == sale_item.Inventory_id).first()
        inventory.Sold_QTY += sale_item.Quantity
        inventory.Locked_QTY -= sale_item.Quantity
    db.session.commit()

    insert_to_cashflow(
        particular=f'Sales ({sale.Type_Payment})',
        debit = sale.Total,
        remark= f'Sales ({sale.Type_Payment}) | Record from: CheckOUT ({datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')})'
    )

    return redirect(url_for("sale.sales_index"))

# def update_inventory
def update_sale_Total(id):
    sale = Sale.query.get_or_404(id)
    subtotal = sum(item.Quantity * item.SalePrice for item in sale.Sale_items)
    # for item in sale.Sale_items:
    #     print(item.Quantity * item.SalePrice)
    #     subtotal += (item.Quantity * item.SalePrice)
    sale.Total = subtotal
    db.session.commit()



@bp.route('/detail',methods=['GET'])

@login_required
def get_sale_detail():
    date = request.args.get('date')
    # sales = Sale.query.filter(Sale.Date == date,Sale.Status == "paid").all()
    sales = Sale.query.filter(Sale.Date == date,Sale.Status=='paid').order_by(Sale.Date).all()
    users = User.query.all()
    products = Product.query.all()
    
    # print(product)
    return render_template('sales/saledetail.html',sales = sales,products=products,users=users,date = date,str=str)

