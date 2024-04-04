from datetime import date, datetime, time, timedelta
import math
import string
from flask import Flask, Blueprint, redirect, render_template, request, url_for
from numpy import equal
from app import update_qty_on_expiry
from app.extensions import db
from app.models.cashflow import Cashflow
bp = Blueprint('cashflow',__name__)

def init_current_month():
    update_qty_on_expiry()
    first_day_of_month, last_day_of_month, firstday_of_previous_month, last_month_end = get_month_value(datetime.now())

    # Filter last record of previous month
    last_month_records = Cashflow.query.filter(
        Cashflow.date >= firstday_of_previous_month,
        Cashflow.date < first_day_of_month
    ).order_by(Cashflow.date.desc()).all()

    # Check the last balance of previous month, if record exist then assign LAST BALANCE
    last_debit = 0
    if last_month_records:

        last_debit = last_month_records[0].balance

    #create first record of current month
    if not Cashflow.query.filter(Cashflow.date == first_day_of_month).first():
        new_cashflow = Cashflow(particulars = "balance b/f",date = first_day_of_month, debit=last_debit)
        db.session.add(new_cashflow)
        db.session.commit()
        new_cashflow.balance = new_cashflow.debit - new_cashflow.credit
        db.session.commit()


@bp.route('/', methods=['GET'])
def index():
    inncashflow()
    print("tyesss")
    selected_month =  datetime.today() if not request.args.get('date') else datetime.strptime(request.args.get('date'),'%Y-%m').replace(day=1).date()
    selected_month = datetime.strftime(selected_month,'%Y-%m-%d')
    selected_month = datetime.strptime(selected_month,"%Y-%m-%d").replace(day=1,hour=0,minute=0,second=0)

    first_day_of_month, last_day_of_month, _,_ = get_month_value(datetime.now())
    if not Cashflow.query.filter(Cashflow.date == first_day_of_month).first():
        init_current_month()

    check_last_month_balance(first_day_of_month)
    
    first_day_of_month, last_day_of_month, firstday_of_previous_month, lastday_of_previous_month = get_month_value(selected_month)
    cashflows = Cashflow.query.filter(Cashflow.date >= first_day_of_month,Cashflow.date<=last_day_of_month).order_by(Cashflow.date).all()
    return render_template('cashflow.html',cashflows = cashflows,date = datetime.strftime(selected_month,'%Y-%m'))



def get_month_value(date):
    
    '''
    return 4 value,
    return type: Datetime
    '''
    
    # first day of current month
    first_day_month = datetime.strftime(date,"%Y-%m-%d %H:%M:%S")
    first_day_month = datetime.strptime(first_day_month,"%Y-%m-%d %H:%M:%S").replace(day=1,hour=0,minute=0,second=0)

    #last day of current month
    next_month = first_day_month.replace(day=28) + timedelta(days=4)
    lastday_of_month = next_month.replace(day=1) - timedelta(days=1)
    lastday_of_month = lastday_of_month.replace(hour=23,minute=59,second=59)

    # get first day and last day of previous month
    lastday_of_previous_month = first_day_month.replace(day=1) - timedelta(days=1)
    lastday_of_previous_month = lastday_of_previous_month.replace(hour=23,minute=59,second=59)
    firstday_of_previous_month = lastday_of_previous_month.replace(day=1,hour=0,minute=0,second=0)
    return first_day_month, lastday_of_month, firstday_of_previous_month, lastday_of_previous_month

def round_to(value, decimals=9):
    return eval(f"{{:.{decimals}f}}".format(value))

def check_last_month_balance(date):
    first_day_month, lastday_of_month, firstday_of_previous_month, lastday_of_previous_month = get_month_value(date)
    cashflow = Cashflow.query.filter(Cashflow.date == first_day_month).first()
    last_record = get_last_record_before_date(first_day_month)
    if last_record:
        cashflow.debit = float(last_record.balance)
        cashflow.balance = float(cashflow.debit)
        db.session.commit()

            # Update balance for affected records
        affected_records = Cashflow.query.filter(Cashflow.date >= cashflow.date,Cashflow.date<=lastday_of_month).order_by(Cashflow.date).all()
        for record in affected_records:
            if record.id != cashflow.id:
                last_record = get_last_record_before_date(record.date)
                # balance_change = cashflow.balance - last_record.balance
                # record.balance += balance_change
                record.balance = last_record.balance + (record.debit - record.credit)
            db.session.commit()
    else:
        print("NO previous record", last_record)
        # print(cashflow.balance)






@bp.route('/detail',methods=["GET"])
# @bp.route('/detail/<int:id>',methods=["GET"])
def record_detail():
    id = request.args.get('id',type=int)
    cashflow = Cashflow.query.filter(Cashflow.id == id).first()
    return render_template('cashflow_detail.html',cashflow = cashflow)




def get_last_record_before_date(date):
    return Cashflow.query.filter(Cashflow.date < date).order_by(Cashflow.date.desc()).first()

@bp.route('/', methods=['POST'])
def add_cashflow():


    specific_date = datetime.strftime(datetime.today(),"%Y-%m-%d %H:%M:%S")
    specific_date = datetime.strptime(specific_date,"%Y-%m-%d %H:%M:%S")
    last_record = get_last_record_before_date(specific_date)
    
    # print(f"{last_record.date} + {last_record.balance}")
    if last_record:
        last_balance = last_record.balance
    else:
        last_balance = 0

    new_cashflow = Cashflow(
        particulars=request.form['particulars'],
        date=specific_date,
        debit=request.form['debit'],
        credit=request.form['credit'],
        remarks=request.form['remark']
    )
    new_cashflow.balance =float(last_balance) + float(new_cashflow.debit) - float(new_cashflow.credit)
    db.session.add(new_cashflow)
    db.session.commit()

    affected_records = Cashflow.query.filter(Cashflow.date > specific_date).order_by(Cashflow.date).all()
    for record in affected_records:
            record.balance = record.balance + new_cashflow.debit - new_cashflow.credit

    db.session.commit()
    return redirect(url_for('cashflow.index'))




@bp.route('/insert_record', methods=['POST'])
def insert_cashflow():
    new_date = datetime.strptime(request.form['new_date']+ ' ' + request.form['new_time'],'%Y-%m-%d %H:%M:%S')
    last_record = get_last_record_before_date(new_date)
    _,lastday_of_month,_,_ = get_month_value(new_date)
    try:
        new_cashflow = Cashflow(
            particulars=request.form['particulars'],
            date=new_date,
            debit=request.form['debit'],
            credit=request.form['credit'],
            remarks=request.form['remark']
        )
        db.session.add(new_cashflow)
        db.session.commit()

        
        affected_records = Cashflow.query.filter(Cashflow.date > last_record.date, Cashflow.date <= lastday_of_month).order_by(Cashflow.date).all()
        
        for record in affected_records:
            last_record = get_last_record_before_date(record.date)
            record.balance = last_record.balance + (record.debit - record.credit)
                    # record.balance = last_record.balance + (record.debit - record.credit)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"error: {str(e)}", 500

    return redirect(url_for('cashflow.index'))

def insert_to_cashflow(particular='',debit=0.00,credit=0.00,remark=''):
    print('yessss')
    date = datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')
    date = datetime.strptime(date,'%Y-%m-%d %H:%M:%S')
    first_day_of_month, last_day_of_month, _,_= get_month_value(date)
    if not Cashflow.query.filter(Cashflow.date == first_day_of_month).first():
        init_current_month()
        check_last_month_balance(date)

    last_record = get_last_record_before_date(date)
    new_cashflow = Cashflow(
        particulars = particular,
        debit = debit,
        credit = credit,
        date = date,
        remarks = remark
    )
    db.session.add(new_cashflow)
    db.session.commit()
    new_cashflow.balance = last_record.balance + (new_cashflow.debit - new_cashflow.credit)
    db.session.commit()
    print('end eeeee')
    

#This Method is used to update the record without date
@bp.route('/detail',methods=["POST"])
def update_record():
    id = request.args.get('id',default=None,type=int)
    if not id:
        return 404
    # Find current record
    cashflow = Cashflow.query.filter_by(id=id).first_or_404()
    #get previous record
    previous_record = Cashflow.query.filter(Cashflow.date<cashflow.date,Cashflow.date>=cashflow.date.replace(day=1,hour=0,minute=0,second=0)).order_by(Cashflow.date.desc()).first()
    last_balance = 0
    if previous_record:
        last_balance = previous_record.balance #get previous balance


    new_credit = request.form["new_credit"]
    new_debit = request.form["new_debit"]
    new_remark = request.form["new_remark"]

    old_amount = cashflow.balance
    new_balance = float(last_balance) + float(new_debit) - float(new_credit)
    cashflow.balance = new_balance
    cashflow.particulars = request.form['new_particular']
    cashflow.debit = new_debit
    cashflow.credit = new_credit
    cashflow.remarks = new_remark
    db.session.commit()
    


    # Update balance for affected records
    affected_records = Cashflow.query.filter(Cashflow.date >= cashflow.date).all()
    for record in affected_records:
        if record.id != cashflow.id:
            balance_change = new_balance - old_amount
            record.balance += balance_change
    db.session.commit()
    return redirect(url_for('cashflow.index'))


#This Method is used to update the record date
@bp.route('/update', methods=['POST'])
def update_cashflow_date():
    id = request.args.get('id')
    cashflow = Cashflow.query.get_or_404(id)
    new_date = datetime.strptime(request.form['new_date']+ ' ' + request.form['new_time'],'%Y-%m-%d %H:%M:%S')
    old_date = cashflow.date

    if not new_date:
        return redirect(url_for('cashflow.index'))
    _, lastday_of_month, _,_ = get_month_value(new_date)

    if new_date< old_date:
        last_record = get_last_record_before_date(new_date)
    else:
        last_record = get_last_record_before_date(old_date)

    # print('last: ',last_record.balance)

    try:
        cashflow.date = new_date
        cashflow.balance = last_record.balance + (cashflow.debit - cashflow.credit)
        db.session.commit()
        affected_records = Cashflow.query.filter(Cashflow.date > last_record.date, Cashflow.date <= lastday_of_month).order_by(Cashflow.date).all()
        
        for record in affected_records:
            last_record = get_last_record_before_date(record.date)
            record.balance = last_record.balance + (record.debit - record.credit)
                    # record.balance = last_record.balance + (record.debit - record.credit)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"error: {str(e)}", 500
    return redirect(url_for('cashflow.index'))



@bp.route('/delete/<int:cashflow_id>', methods=['GET'])
def delete_cashflow(cashflow_id):
    cashflow = Cashflow.query.get_or_404(cashflow_id)
    affected_records = Cashflow.query.filter(Cashflow.date >= cashflow.date).all()

    try:
        db.session.delete(cashflow)
        for record in affected_records:
            if record.id != cashflow_id:
                if cashflow.debit > 0:
                    record.balance -= cashflow.debit
                else:
                    record.balance += cashflow.credit

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"Eror: 500"
    return redirect(url_for('cashflow.index'))



def inncashflow():

    c = Cashflow.query.all()
    if c:
        return print('Got data')
    first_day_month, lastday_of_month, firstday_of_previous_month, lastday_of_previous_month = get_month_value(datetime.now())
    cashflow = Cashflow.query.filter(Cashflow.date == lastday_of_previous_month).first()
    if not cashflow:
        new_cashflow = Cashflow(
            particulars = 'Last_Balance',
            debit = 0,
            credit = 0,
            date = lastday_of_previous_month,
            balance = 0,
            remarks = ''
        )
        db.session.add(new_cashflow)
        db.session.commit()

    return print('Create data successfully')