from datetime import datetime
from app.dailySalesReport import bp
from app.models.dailysalesreport import DailySalesReport,Sale
from flask import render_template, request, redirect, url_for
from app import db

@bp.route('/')
def index():
    today_date = datetime.today().strftime('%Y-%m-%d')
    reports = DailySalesReport.query.all()
    report = db.metadata.tables["daily_sales_report"]
    # today_records = db.session.execute(db.select(report).filter_by(Date = today_date)).fetchall()
    # today_sales = (
    # db.session.query(Sale.Product_name,Sale.Quantity, Sale.Subtotal)
    #     .join(DailySalesReport, DailySalesReport.id == Sale.Report_id)
    #     .filter(DailySalesReport.Date == today_date)
    #     .all()
    # )
    # # today_sales = SalesDetails.query.filter(Date = today_date and )
    # return render_template('sales/index.html', action="", 
    #                        reports = reports,column_names=report.columns.keys(),
    #                        today_records=today_records,
    #                        today_sales = today_sales
    #                        )



@bp.route('/create', methods=['GET','POST'])
def create_dailysalesreport():
    StaffID = "000001" 
    if request.method == 'POST':
        
        
        return redirect(url_for('dailysalesreport.index'))
     
    # if request.method == 'GET':
    #     reports = DailySalesReport.query.all()
    #     today_report = db.session.execute(db.select(db.metadata.tables['daily_sales_report']).filter(DailySalesReport.StaffID == StaffID,DailySalesReport.Date == datetime.today().strftime('%Y-%m-%d'))).first()
    #     # today_report = DailySalesReport.query.filter(DailySalesReport.Date == datetime.today().strftime('%Y-%m-%d')).all()
    #     # today_sales = db.session.execute(db.select(db.metadata.tables['sales_details']).filter(SalesDetails.Report_id == today_report.id)).fetchall()
    #     if today_report:
    #         print("yes")
    #         salesdetail = Sale(daily_sales_report = today_report.id,Product_name="100 plus 350ml",Quantity=2,SalePrice=2.50,Subtotal=5.00)
    #         db.session.add(salesdetail)
    #         db.session.commit()
    #     else: 
    #         print("no")
    #         new_report = DailySalesReport(StaffID,datetime.today(),0)
    #         db.session.add(new_report)
    #         db.session.commit()
    #     # print(today_sales)
    #     # for index, t in enumerate(today_report):

    #     #     print(t)
    #     #     print(today_report[index].Date)
    return ""
    

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_dailysalesreport(id):
    report = DailySalesReport.query.get_or_404(id)

    if request.method == 'POST':
        # Update data from the form
        

        
        # Commit changes to the database
        db.session.commit()

    reports = DailySalesReport.query.all()
    return render_template('report/index.html',action = 'edit_report',reports = reports)

@bp.route('/<int:id>/delete', methods=['POST'])
def delete_dailysalesreporty(id):
    report = DailySalesReport.query.get_or_404(id)

    # Delete the inventory item from the database
    db.session.delete(report)
    db.session.commit()

    return redirect(url_for('dailysalesreport.index'))

