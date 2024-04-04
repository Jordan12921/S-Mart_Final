
from datetime import date
from flask_login import login_required
from app.models.category import Category
from app.models.supplier import Supplier
from app.product import bp
from flask import flash, render_template, request, redirect, url_for
from app.models.product import Product
from app import db, update_qty_on_expiry

from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, SelectMultipleField, StringField, ValidationError
from wtforms.validators import InputRequired,Optional

from app.product.inventory_routers import InventoryForm
from flask_principal import Permission,RoleNeed

admin_permission = Permission(RoleNeed('admin'))
class CreateProductForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    barcode = StringField('BarCode', validators=[InputRequired()])
    safety_quantity_custom = BooleanField('Custom Set Line')
    safety_quantity = IntegerField('Safety Quantity', validators=[Optional()])
    status = SelectField('Status', choices=[('NotAvailable', 'Not Available'), ('OutOfStock', 'Out of Stock'), ('InStock', 'In Stock')], default='NotAvailable')
    categories = SelectMultipleField('Categories', choices=[], coerce=int)

    def __init__(self, *args, **kwargs):
        super(CreateProductForm, self).__init__(*args, **kwargs)
        self.categories.choices = [(category.id, category.Name) for category in Category.query.all()]

@bp.route('/',methods=["GET"])
@login_required
def index():
    update_qty_on_expiry()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query = request.args.get('query','')

    form = CreateProductForm()
    categories = Category.query.all()
    # form.set_category_choices(categories)
    if query:
        products = Product.query.filter(
            db.or_(Product.BarCode.ilike(f'%{query}%'), Product.Name.ilike(f'%{query}%'))
        ).paginate(per_page=per_page, page=page, error_out=True)
    else:
        products = Product.query.all()

    categories = Category.query.all()
    
    return render_template('product/product.html', products=products,categories=categories,form=form)


@bp.route('/category/<category_name>')
@login_required
def products_by_category(category_name):
    # Query the Category table to find the category with the given name
    category = Category.query.filter_by(Name=category_name).first()
    column_names = Product.metadata.tables['product'].columns.keys()
    categories = Category.query.all()
    form = CreateProductForm()
    if category:
        # If the category exists, retrieve all products associated with it
        products = category.products
        return render_template('product/product.html', products=products, column_names=column_names,categories=categories,form=form)
    else:
        # If the category does not exist, return an error message or handle it as you wish
        return "Category not found", 404


@bp.route('/<int:id>', methods=['GET'])
@login_required
def get_product(id):

    if not id:
        id = request.args.get('id')
    product = db.one_or_404(db.select(Product).filter(Product.id == id))
    suppliers = Supplier.query.all()
    inventories = product.Inventories
    categories = Category.query.all()
    form = CreateProductForm(obj=product)
    form.categories.choices = [(category.id, category.Name) for category in Category.query.all()]

    inventoryForm = InventoryForm()
    inventoryForm.supplier.choices = [(supplier.id,supplier.Name) for supplier in suppliers]

    return render_template('product/detail.html', product=product,categories = categories,inventories = inventories,suppliers=suppliers,form = form,inventoryForm=inventoryForm,date=date)

   


@bp.route('/search/', methods=['GET'])
@login_required
def search_product():
    categories = Category.query.all()
    products = Product.query.all()
    query = request.args.get('query','')
    form = CreateProductForm()
    if not query:
        return redirect(url_for('product.index'))
    
    products = Product.query.filter(
        db.or_(Product.BarCode.ilike(f'%{query}%'), Product.Name.ilike(f'%{query}%'))
    ).all()
    

    return render_template('product/product.html',  products=products,categories=categories,form=form)




    
@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=401)
def create_product():
    form = CreateProductForm()
    categories = Category.query.all()
    # form.set_category_choices(categories)


    if form.validate_on_submit():
        name = form.name.data
        barcode = form.barcode.data
        safety_quantity = form.safety_quantity.data if form.safety_quantity_custom.data else -1
        status = form.status.data
        
        new_product = Product(
            Name=name, 
            BarCode=barcode, 
            Safety_quantity=safety_quantity, 
            Status=status
        )
        
        # Add categories to the product
        for category_id in form.categories.data:
            category = Category.query.get(category_id)
            if category:
                new_product.Categories.append(category)

        
        db.session.add(new_product)
        db.session.commit()
        flash('Product created successfully!', 'success')

        return redirect(url_for('product.index'))

    return render_template('product/product.html',products = Product.query.all(),categories = categories,form = form)

    
@bp.route('/quick_edit/<barcode>', methods=['GET', 'POST'])
@login_required
def quick_edit(barcode):
    # product = db.one_or_404(db.select(Product).filter_by(BarCode=barcode))
    product = Product.query.filter_by(BarCode=barcode).first_or_404()
    form = CreateProductForm(obj = product)
    if form.validate_on_submit():
        product.BarCode = form.barcode.data
        product.Name = form.name.data
        product.Safety_quantity = form.safety_quantity.data
        try:
            # Commit changes to the database
            db.session.commit()
        except Exception as e:
            db.session.rollback()
        return redirect(url_for('product.index'))
    
    return render_template('product/product.html',products = Product.query.all(),categories = Category.query.all(),form = form)



@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    if not id:
        id = request.args.get('id')
    product = Product.query.filter_by(id = id).first_or_404()
    categories = Category.query.all()
    suppliers = Supplier.query.all()
    form = CreateProductForm(obj=product)
    inventoryForm = InventoryForm()
    form.categories.choices = [(category.id, category.Name) for category in Category.query.all()]

    if request.method == 'POST':
        if "save_category" in request.form:
            product.Categories.clear()
            for category_id in form.categories.data:
                product.Categories.append(Category.query.filter(Category.id == category_id).first())
            
        else:
            product.BarCode = form.barcode.data
            product.Name = form.name.data
            product.Safety_quantity = form.safety_quantity.data if form.safety_quantity_custom.data and form.safety_quantity.data else -1
            product.Status = form.status.data if form.status.data else product.Status

        try:
            db.session.commit()
            return redirect(url_for('product.get_product',barcode=product.BarCode))
        except Exception as e:
            db.session.rollback()
            flash("Error occurred while updating the product.", "error")

    return render_template('product/detail.html', product=product,categories = categories, suppliers = suppliers ,form=form,inventoryForm=inventoryForm ,date =date)


@bp.route('/product/<int:id>/delete')
@login_required
@admin_permission.require(http_exception=401)
def delete_product(id):
    product = Product.query.get_or_404(id)
    product.delete()
    return redirect(url_for('product.index'))


def insert_data_to_product(df):
    try:
        for index, row in df.iterrows():
            # Create a new User object for each row of data
            product = Product.query.filter(Product.Name == row['Name'],Product.BarCode==row['BarCode']).first()
            if product:
                continue
            product = Product(
                BarCode=row['BarCode'],
                Name=row['Name'],
                Safety_quantity=row['Safety_quantity'],
                Status=row['Status']
                # Add other columns as needed
            )
            

            db.session.add(product)  # Add the user to the session

        db.session.commit()  # Commit all changes to the database
        return True, None  # Return success
    except Exception as e:
        db.session.rollback()  # Rollback changes if an error occurs
        return False, str(e) 

