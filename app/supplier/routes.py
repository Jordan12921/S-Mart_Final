
from flask_login import login_required
from app.supplier import bp
from flask import render_template, request, redirect, url_for
from app.models.supplier import Supplier
from app import db, update_qty_on_expiry


# Create Supplier
@bp.route('/add', methods=['POST'])
@login_required
def add_supplier():
    update_qty_on_expiry()
    name = request.form['name']
    contact = request.form['contact']
    address = request.form['address']
    comment = request.form['comment']

    # Validation checks can be added here

    supplier = Supplier(Name=name, Contact=contact, Address=address, Comment=comment)
    db.session.add(supplier)
    db.session.commit()
    return redirect(url_for('supplier.index'))

# Read Supplier
@bp.route('/<int:id>')
@login_required
def get_supplier(id):
    supplier = Supplier.query.get(id)
    return render_template('supplier/detail.html', supplier=supplier)

# Update Supplier
@bp.route('/update/<int:id>', methods=['POST'])
@login_required
def update_supplier(id):
    supplier = Supplier.query.get(id)
    supplier.Name = request.form['name']
    supplier.Contact = request.form['contact']
    supplier.Address = request.form['address']
    supplier.Comment = request.form['comment']
    db.session.commit()
    return redirect(url_for('supplier.index'))

# Delete Supplier
@bp.route('/delete/<int:id>')
@login_required
def delete_supplier(id):
    supplier = Supplier.query.get(id)
    db.session.delete(supplier)
    db.session.commit()
    return redirect(url_for('supplier.index'))

# Search Supplier
@bp.route('/search')
@login_required
def search_supplier():
    keyword = request.args.get('q','')
    suppliers = Supplier.query.filter(Supplier.Name.ilike(f'%{keyword}%')).all()
    return render_template('supplier/index.html', suppliers=suppliers)

# Pagination Supplier
@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page =  request.args.get('per_page', 10, type=int)
    suppliers = Supplier.query.paginate(page = page, per_page = per_page, error_out=False)
    return render_template('supplier/index.html', suppliers=suppliers)