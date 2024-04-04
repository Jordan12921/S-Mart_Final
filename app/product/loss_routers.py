from datetime import date, datetime
from flask import flash, redirect, request, url_for,render_template
from flask_login import login_required
from app.models.product import LostReport, Product,Inventory
from app import db
from app.product import bp
from flask_principal import Permission,RoleNeed
admin_permission = Permission(RoleNeed('admin'))

@bp.route('/lost_report', methods=['POST'])
def create_lost_report():
    id = request.args.get('i',None,int)
    inventory = Inventory.query.filter(Inventory.id == id).first()
    
    particular = request.form['particular']
    quantity_lost = int(request.form['lost_qty'])
    remark = request.form['remark']
    date = datetime.strftime(datetime.now(),'%Y=%m-%d %H:%M:%S')
    if not inventory:
        flash('error: Inventory not found', 'message')

    if not inventory.Available_QTY >= quantity_lost:
        flash("error: Insufficient quantity in inventory","message")
    
    inventory.Available_QTY -= quantity_lost
    inventory.Lost_QTY += quantity_lost
    db.session.add(LostReport(particulars=particular,
                                inventory_id=id,
                                date = datetime.strptime(date,'%Y=%m-%d %H:%M:%S'),
                                qty_lost=quantity_lost, 
                                remark=remark))
    db.session.commit()
    return redirect(url_for('product.inventory_detail',id = inventory.id))

        

        
    


@bp.route('/inventory/undo/<int:id>', methods=['GET'])
@login_required
@admin_permission.require(http_exception=401)
def undo_items(id):
    print('id:',id)
    if not id:
        
        id = request.args.get('id',None,int)
        print('id:',id)

    lost_record = LostReport.query.get_or_404(id)
    inventory = Inventory.query.get_or_404(lost_record.inventory_id)

    if not lost_record and inventory:
        return "Notfound 404"

    if not inventory.ExpiryDate > date.today():
        flash('The undo operation failed, inventory has expired.', 'error')
        return redirect(url_for('product.inventory_detail',id = inventory.id))
    
    print('inside date checked')
    inventory.Lost_QTY -= lost_record.qty_lost
    inventory.Available_QTY += lost_record.qty_lost
    try:
        db.session.delete(lost_record)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        

    return redirect(url_for('product.get_product',id = inventory.Product_id))