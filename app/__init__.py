from datetime import date, datetime, timedelta
import os
from statistics import mean
from flask import Flask, render_template, request, redirect, send_file, url_for
from flask_login import current_user, login_required
from sqlalchemy import extract,cast, Date, func, Integer

from config import Config
from app.extensions import db

from app.models.supplier import Supplier
from app.models.category import Category
from app.models.user import User
from app.models.product import Product,Inventory,LostReport
from app.models.supplier import Supplier
from app.models.sale import Sale,Sale_Item
from app.models.cashflow import Cashflow

from app.plotly_graphs import *
from flask_principal import UserNeed,RoleNeed,identity_loaded
def check_inventory():
    # products_below_safety = Product.query.filter(Product.Safety_quantity > Product.Inventories.any(Inventory.Available_QTY)).all()
    products = Product.query.filter(Product.Safety_quantity>=0).all()
    
    products_below_safety = db.session.query(Product.id,Product.Name,Product.Safety_quantity,db.func.sum(Inventory.Available_QTY).label('Available_QTY')).filter(Product.id == Inventory.Product_id).group_by(Product.id).having(db.func.sum(Inventory.Available_QTY) < Product.Safety_quantity).all()
    # Count the number of products below safety line
    count_below_safety = len(products_below_safety)
    # products_below_safety = db.session.query(Product).filter(
    # Product.Safety_quantity > (
    #     db.session.query(db.func.sum(Inventory.Available_QTY))
    #     .filter(Inventory.Product_id == Product.id)
    #     .scalar()
    # )).all()

    # products_below_safety = (
    #     db.session.query(Product.Name, db.func.sum(Inventory.Available_QTY).label('Available_QTY'))
    #     .join(Inventory, Product.id == Inventory.Product_id)
    #     .group_by(Product.id)
    #     .having(db.func.sum(Inventory.Available_QTY) < Product.Safety_quantity)
    #     .all()
    # )
    print(products_below_safety)
    return products_below_safety, count_below_safety



def create_app(config_class = Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    # app.config['SECRET_KEY'] = 'smart_key_fyp_project'
    #Initialize Flask extensions here
    from app.extensions import init_extensions
    init_extensions(app)  
    # Register blueprints her

    from app.main import main as main_bp
    app.register_blueprint(main_bp)

    from app.category import bp as category_bp
    app.register_blueprint(category_bp,url_prefix='/category')

    from app.product import bp as product_bp
    app.register_blueprint(product_bp, url_prefix='/products')

    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/staff')
    
    from app.utils import bp as utils_bp
    app.register_blueprint(utils_bp, url_prefix='/utils')

    # from app.dailySalesReport import bp as sales_bp
    # app.register_blueprint(sales_bp, url_prefix='/daily_reports')
    from app.sale import bp as sales_bp
    app.register_blueprint(sales_bp, url_prefix='/sales')
    from app.supplier import bp as supplier_bp
    app.register_blueprint(supplier_bp, url_prefix='/suppliers')

    from app.auth import auth as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.cashflow.routes import bp as cashflow_bp
    app.register_blueprint(cashflow_bp, url_prefix='/cashflow')
    
    

    app.jinja_env.filters['has_role'] = has_role
        
    @app.route('/')
    @login_required
    def dashboard():
        # inventories = Inventory.query.all()
        # categories = Category.query.all()
        # products = Product.query.all()
        # Monthly Profit
        update_qty_on_expiry()

        product_proportion = show_product_proportion_pie()
        sales_graph = show_sales_graph()
        turnover_bar = show_inventory_turnover_graph()
        vertical_product_bar = show_prodcut_vertical_bar()
        lost_cost_bar = show_product_lost_cost_bar()

    
        # Convert the pie chart to JSON format
        product_proportion_pie = product_proportion.to_json()
        sales_graph = sales_graph.to_json()
        turnover_bar = turnover_bar.to_json()
        vertical_product_bar = vertical_product_bar.to_json()

        lost_cost_bar =lost_cost_bar.to_json()
        product_count,sale_count,total_supplier,total_staff = all_Model_value_total()

        product_lost = db.session.query(Product.Name,
                                        Inventory.Lost_QTY,
                                        Inventory.CostPerItem).filter(Inventory.ExpiryDate>=date.today(),Inventory.Lost_QTY>0, Inventory.Product_id == Product.id)
        
        # Get today's date
        today = datetime.today().date()

        # Calculate the date 30 days from today
        thirty_days_from_now = date.today() + timedelta(days=30)

        # Query to get items with ExpiryDate within the next 30 days
        product_threshold = db.session.query(
            Product.Name,
            Inventory.ExpiryDate,
            Inventory.Available_QTY,
            Inventory.RetailPrice,
            cast((func.julianday(func.DATE(Inventory.ExpiryDate)) - func.julianday(today)), Integer).label("days_to_expiry")
        ).join(Product).filter(
            # Ensure that ExpiryDate is greater than or equal to today
            # And less than or equal to thirty days from now
            func.DATE(Inventory.ExpiryDate) >= today,
            func.DATE(Inventory.ExpiryDate) <= thirty_days_from_now
        ).group_by(Product.Name).order_by(Product.Name).all()
        
        products_below_safety , count_below_safety = check_inventory()
        
        
        # total_suppkier = Supplier.query(db.func.sum())
        return render_template('index.html', sales_graph = sales_graph,
                               product_proportion_pie= product_proportion_pie,
                               turnover_bar = turnover_bar,
                               vertical_product_bar=vertical_product_bar,
                               lost_cost_bar = lost_cost_bar,
                               inventory_warning = products_below_safety,
                               count_below_safety = count_below_safety,
                               product_count = product_count,sale_count = sale_count,total_supplier = total_supplier,total_staff = total_staff,
                               product_lost = product_lost,
                               product_threshold = product_threshold
        
        )
        
        
    
    @app.route('/template/download')
    def download_file():
        template_name = request.args.get('file_name')
        print(os.pardir)
        basedir = os.path.abspath(os.path.dirname(__file__))  # Get the absolute path of the current directory
        project_dir = os.path.abspath(os.path.join(basedir, os.pardir))  # Move one directory up to 'F:\\python project\\project2'
        file_path = os.path.join(project_dir, f"{template_name}.xlsx")
        # Replace 'path/to/your/file' with the actual path to your file
        return send_file(file_path, as_attachment=True)
    


    @app.route('/init_data')
    def initdata():
        product_table = db.metadata.tables["product"]
        # query = db.session.execute(db.select(product_table).filter_by(BarCode=3927110))
        query = Product.query.filter(Product.BarCode == "3927110")
        # product =  db.one_or_404(db.select(product_table).filter_by(BarCode=3927110))
        product = query if query.first() else None
        print(product)
        with app.app_context():
            staff = User(Name="admin",Email="admin@mail.com",Password="su",Role="admin")
            supplier = Supplier(Name="K Company",Address="Unkown Address")
            db.session.add_all([staff])
            db.session.add_all([supplier])
            db.session.commit()
            
            product1 = Product( BarCode = "3927110",Name = "KitKat",Safety_quantity = -1,Status="NotAvailable")
            inventory1 = Inventory(product = product1,Supplier_id = supplier.id,StockInDate = datetime.strptime("2024-2-2", '%Y-%m-%d'),ExpiryDate = datetime.strptime("2025-4-30", '%Y-%m-%d'),Init_QTY=100,Available_QTY=100,Locked_QTY= 0,Lost_QTY=0,Sold_QTY=0,CostPerItem=2.50,RetailPrice=3.10)
            cat1 = Category(Name="Drink")
            cat2 = Category(Name="Snack")
            cat3 = Category(Name="Chocolate")
            cat4 = Category(Name="Milk")
            cat5 = Category(Name="Discount Packages")
            product1.Categories.append(cat2)
            product1.Categories.append(cat3)
            product1.Categories.append(cat5)

            db.session.add_all([product1])
            db.session.add_all([inventory1])
            db.session.add_all([cat1,cat2,cat3,cat4,cat5])
            db.session.commit()

        return redirect(url_for('/'))
    

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        # Set the identity user object
        identity.user = current_user

        # Add the UserNeed to the identity
        if hasattr(current_user, 'id'):
            identity.provides.add(UserNeed(current_user.id))

        # Assuming the User model has a list of roles, update the
        # identity with the roles that the user provides
        if hasattr(current_user, 'roles'):
            for role in current_user.roles:
                identity.provides.add(RoleNeed(role.name))

    from sqlalchemy import event
    # Define a function to check if a product is expired
    def check_product_expiry(target, connection, **kwargs):
        if target.ExpiryDate and target.ExpiryDate <= date.today():
            print(f"Product '{target.name}' has expired!")

    return app

    


def update_qty_on_expiry():
    inventories = Inventory.query.filter(Inventory.ExpiryDate <= date.today(),Inventory.Available_QTY>0).all()
    if not inventories:
        return
    today_date = datetime.strftime(date.today(),'%Y=%m-%d %H:%M:%S')
    
    for i in inventories:
        i.Lost_QTY += i.Available_QTY
        new_report = LostReport(particulars="Items Expired",
                                inventory_id=i.id,
                                date = datetime.strptime(today_date,'%Y=%m-%d %H:%M:%S'),
                                qty_lost=i.Available_QTY, 
                                remark=f"Product Items Expired, Expiry Date: {i.ExpiryDate}")
        i.Available_QTY = 0
        db.session.add(new_report)
        db.session.commit()









def has_role(roles, target_role):
    return any(role.name == target_role for role in roles)


def all_Model_value_total():
    total_supplier = Supplier.query.count()
    total_staff = User.query.count()
    total_products = Product.query.count()
    total_inventories = Inventory.query.count()
    total_categories = Category.query.count()
    out_of_stock_products = Product.query.filter_by(Status='OutOfStock').count()
    not_available_products = Product.query.filter_by(Status='NotAvailable').count()
    in_stock_products = Product.query.filter_by(Status='InStock').count()
    total_sold = db.session.query(db.func.sum(Inventory.Sold_QTY)).scalar()
    total_inventory_cost = db.session.query(db.func.sum(Inventory.CostPerItem * Inventory.Init_QTY)).scalar()
    expired_products = Inventory.query.filter(Inventory.ExpiryDate < date.today()).count()
    inventory_lost = db.session.query(db.func.sum(Inventory.Lost_QTY)).scalar()
    lost_cost = db.session.query(db.func.sum(Inventory.CostPerItem * Inventory.Lost_QTY)).scalar()


    # Sales Count
    total_sales = Sale.query.count()
    # Calculate total monthly profit
    current_month = datetime.now().month
    current_year = datetime.now().year
    # total_monthly_profit = db.session.query(db.func.sum(Sale.Total - (Sale_Item.Quantity * Inventory.CostPerItem))) \
    #     .join(Sale_Item).join(Inventory).filter(db.func.extract('year', Sale.Date) == current_year, db.func.extract('month', Sale.Date) == current_month).scalar()
    total_monthly_profit = db.session.query(db.func.sum(Sale.Total)).filter(db.func.extract('year', Sale.Date) == current_year, db.func.extract('month', Sale.Date) == current_month).scalar()


    # Calculate daily sales and daily profit
    today = date.today()
    total_daily_sales = Sale.query.filter_by(Date=today).count()
    # total_daily_profit = db.session.query(db.func.sum(Sale.Total - (Sale_Item.Quantity * Inventory.CostPerItem))) \
    #     .join(Sale_Item).join(Inventory).filter(Sale.Date == today).scalar()
    
    total_daily_profit = db.session.query(db.func.sum(Sale.Total)).filter(Sale.Date == today).scalar()
    

    # Create plotly visualization for products by status
    product_count = {'total':total_products,
                     'categories':total_categories,
                     'OutOfStock': out_of_stock_products, 
                     'NotAvailable': not_available_products,
                     'total_inventories':total_inventories,
                     'total_sold':total_sold,
                     'in_stock_products':in_stock_products,
                     'total_inventory_cost': total_inventory_cost,
                     'expired':expired_products,
                     'inventory_lost':inventory_lost,
                     'lost_cost':lost_cost
                     }
    
    sale_count = {'total_sales':total_sales,
                  'total_monthly_profit': "%.2f" % total_monthly_profit if total_monthly_profit else 0,
                  'total_daily_sales':total_daily_sales,
                  'total_daily_profit':  "%.2f" % total_daily_profit if total_daily_profit else 0
                  }
    return product_count,sale_count,total_supplier,total_staff

if __name__ == "__main__":
    app = create_app()

    app.run(port=5001)