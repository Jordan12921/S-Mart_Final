from datetime import datetime
from flask import Blueprint, current_app, flash,render_template,redirect, request, session, url_for
from flask_login import current_user, login_user, login_required, logout_user
from flask_wtf import FlaskForm

# from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db,login_manager
from app.models.user import Role, User, UserRoles

from flask_principal import Principal, Identity, AnonymousIdentity, identity_changed
from werkzeug.security import  check_password_hash


from wtforms import BooleanField, IntegerField, PasswordField, RadioField, SelectField, StringField, ValidationError
from wtforms.validators import InputRequired,Email, Length, EqualTo,NumberRange,DataRequired

auth = Blueprint('auth', __name__)
 

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=5)])
 
class ForgetForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=50)])
    pins = IntegerField('Security Pin', validators=[InputRequired(),Length(min=6,max=6)])
    
    def validate_email(self, field):
        if not User.query.filter(User.Email == field.data, User.pins == field.data).first():
            raise ValidationError('Email doest not existing.')



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth.route('/login', methods=['GET', 'POST']  )
def login():

    form = LoginForm()
    print(form.validate_on_submit())
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        remember = True if request.form.get('remember') else False
        user = User.query.filter_by(Email=email).first()
        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.','error')
            return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page
        
        user.Last_Login = datetime.now()
        db.session.commit()
        login_user(user, remember=remember)


        # Tell Flask-Principal the identity changed
        identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))


        return redirect(url_for('dashboard'))
    

    return render_template('login/login.html',form = form)


@auth.route('/signup',methods=["GET"])
def signup():
    return redirect(url_for('user.create_staff'))
        



@auth.route('/logout')
@login_required
def logout():
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    return redirect(url_for('auth.login'))




@auth.route('/general_reset_password', methods=['POST'])
def general_reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        digits = request.form.get('secret_pin')
        existing_user = User.query.filter(User.Email == email,User.pins == digits).first()
        if not existing_user:
            flash("Email not existed")
            return redirect(url_for('auth.login'))

        existing_user.set_password('123456')
        db.session.commit()
        flash('Password has been reset, Temporary password:123456 \nPlease change your password for security')

    return redirect(url_for('auth.login'))


# @auth.route('/set_pins', methods=['POST'])
# def set_pins():
#     id = request.form.get('id')
#     pins = request.form.get('pins')
#     user = User.query.filter(User.id == int(id)).first()
#     user.pins =pins

#     db.session.commit()
#     return redirect(url_for('main.profile'))