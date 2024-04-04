
from datetime import datetime
from flask_login import current_user, login_required
from app.user import bp
from app.models.user import Role, User
from flask import flash, render_template, request, redirect, url_for
from app import db, update_qty_on_expiry

from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, PasswordField, RadioField, SelectField, StringField, ValidationError
from wtforms.validators import InputRequired,Email, Length, EqualTo,NumberRange,DataRequired
from flask_principal import Permission,RoleNeed
admin_permission = Permission(RoleNeed('admin'))
class CreateStaffForm(FlaskForm):
    id =  StringField('Staff ID', validators=[InputRequired()])
    first_name = StringField('First Name', validators=[InputRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[InputRequired(), Length(max=100)])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=5)])
    pins = IntegerField('Security Pin', validators=[InputRequired(),NumberRange(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(),  EqualTo('password', message='Passwords must match')])

    


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[InputRequired(), Length(min=5, max=80)])
    new_password = PasswordField('New Password', validators=[InputRequired(), Length(min=5, max=80)])
    confirm_password = PasswordField('Confirm New Password', validators=[
        InputRequired(), Length(min=5, max=80), EqualTo('new_password', message='Passwords must match')
    ])
        
class EditStaffForm(FlaskForm):
    id = StringField("Staff ID", validators=[InputRequired()])
    first_name = StringField('First Name', validators=[InputRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[InputRequired(), Length(max=100)])
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=50)])
    pins = IntegerField('Security Pin', validators=[InputRequired(),NumberRange(min=6)])
 
            

        


@bp.route('/')
@login_required
@admin_permission.require(http_exception=401)
def index():
    update_qty_on_expiry()
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    form = EditStaffForm()
    if search_query:
        staffs = User.query.filter(db.or_(User.First_Name.ilike(f'%{search_query}%'),User.Last_Name.ilike(f'%{search_query}'))).paginate(page, per_page=10)
    else:
        staffs = User.query.paginate(page = page, per_page=10)

    return render_template('admin/staff_management.html', staffs=staffs,form =form)

@bp.route('/add', methods=['GET','POST'])
@login_required
@admin_permission.require(http_exception=401)
def create_staff():
    form = CreateStaffForm()
    
    if form.validate_on_submit():

        
        newStaff = User(
            StaffID=form.id.data,
            First_Name=form.first_name.data,
            Last_Name=form.last_name.data,
            Email=form.email.data,
            pins=form.pins.data,
            Email_Confirmed_At = datetime.now()
        )
        newStaff.set_password(form.password.data)
        db.session.add(newStaff)
        db.session.commit()

        role = Role.query.filter_by(id=2).first()
        if role:
            newStaff.roles.append(role)
            db.session.commit()
        else:
            flash('Role not found', 'error')
        db.session.commit()
        return redirect(url_for('user.index'))
 
    return render_template('admin/staff_form.html',form = form,action="add")


@bp.route('/<int:id>/edit', methods=['GET','POST'])
@login_required
def get_staff(id):
    staff = User.query.get_or_404(id)
    form = EditStaffForm(obj=staff)
    pwd_form = ChangePasswordForm()
    print(staff.Last_Name + ' ' + staff.First_Name)

    if form.validate_on_submit():
        staff.StaffID = form.id.data
        staff.First_Name = form.first_name.data
        staff.Last_Name = form.last_name.data
        staff.Email = form.email.data
        staff.pins = form.pins.data
        db.session.commit()
        flash('Staff member updated successfully!', 'success')
        return redirect(url_for('user.index'))
   

    return render_template('admin/staff_form.html',staff = staff,form =  form,pwd_form=pwd_form, id=id, action ="edit")
    


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_permission.require(http_exception=401)
def delete_staff(id):
    staff = User.query.get_or_404(id)
    db.session.delete(staff)
    db.session.commit()
    return redirect(url_for('user.index'))



    

# @bp.route('/<int:id>/quick_edit', methods=['GET','POST'])
# def quick_edit(id):
#     staff = User.query.get_or_404(id)
#     form = EditStaffForm(obj=staff)
#     if request.method =="POST":

#         staff.StaffID = form.id.data
#         staff.First_Name = form.first_name.data
#         staff.Email = form.email.data
#         db.session.commit()
#         flash('Staff member updated successfully!', 'success')
#         return redirect(url_for('user.index'))
#     else:
#         return render_template('admin/staff_management.html',staffs = User.query.all(), form =  form)


@bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    id = request.args.get('id')
    if form.validate_on_submit():
        

        if current_user.check_password(form.old_password.data):
            if form.old_password.data == form.new_password.data:
                flash('New password must be different from the old password.', 'danger')
            else:
                success, message = current_user.change_password(form.old_password.data, form.new_password.data)
                if success:
                    flash(message, 'success')
                else:
                    flash(message, 'danger')
        else:
            flash('Old password is incorrect.', 'danger')
    
    return redirect(url_for('user.get_staff',id = id))


@bp.route('/search')
@login_required
def search_staff():
    keyword = request.args.get('q','')
    staffs = User.query.filter(db.or_(User.StaffID.ilike(f'%{keyword}%'), User.Last_Name.ilike(f'%{keyword}%'),User.First_Name.ilike(f'%{keyword}%'))).all()
    return render_template('admin/staff_management.html', staffs=staffs)



def insert_data_to_staff(df):
    try:
        for index, row in df.iterrows():
            # Create a new User object for each row of data
            user = User.query.filter(User.Last_Name == row['Last_Name'],User.First_Name==row['First_Name'],User.Email==row['Email']).first()
            if user:
                continue
            user = User(
                StaffID=row['StaffID'],
                First_Name=row['First_Name'],
                Last_Name=row['Last_Name'],
                Email=row['Email'],
                # Add other columns as needed
            )
            # Set the user's password (assuming you have a method like set_password)
            user.set_password(row['Password'])
            user.pins = user.generate_pins()

            # Add roles if specified in the DataFrame (you may need to adjust this logic)
            roles = [role.strip() for role in row['roles'].split(',')]
            for role_name in roles:
                role = Role.query.filter_by(name=role_name).first()
                if role:
                    user.roles.append(role)

            db.session.add(user)  # Add the user to the session

        db.session.commit()  # Commit all changes to the database
        return True, None  # Return success
    except Exception as e:
        db.session.rollback()  # Rollback changes if an error occurs
        return False, str(e) 