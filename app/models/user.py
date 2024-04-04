import random
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
#User table DB
class User(UserMixin,db.Model):
    # __tablename__ = "staff"
    # id = db.Column(db.Integer, primary_key=True)
    # Name = db.Column(db.String, unique=True, nullable=False)
    # Email = db.Column(db.String, nullable=False)
    # Password = db.Column(db.String, nullable=False)
    # Role = db.Column(db.String, nullable=False)

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)

    StaffID = db.Column(db.String,unique = True)
    First_Name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    Last_Name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    Email = db.Column(db.String(50), unique=True, nullable=False)
    Password = db.Column(db.String(80), nullable=False)
    pins = db.Column(db.Integer)
    
    roles = db.relationship('Role', secondary='user_roles')
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')
    Email_Confirmed_At = db.Column(db.DateTime())
    Last_Login = db.Column(db.DateTime())
    
    def set_password(self, password):
        self.Password = generate_password_hash(password, method='pbkdf2',salt_length=256)

    def check_password(self, password):
        return check_password_hash(self.Password, password)
    
    def fullname(self):
        return self.Last_Name + ' ' + self.First_Name
    
    def change_password(self, old_password, new_password):
        # Check if the old password matches
        if not self.check_password(old_password):
            return False, "Old password is incorrect."

        # Validate new password
        if len(new_password) < 5:
            return False, "New password must be at least 5 characters long."

        # Update password hash with the new password
        self.set_password(new_password)
        db.session.commit()
        return True, "Password updated successfully."
    
    def generate_pins(self):
        return random.randint(100000, 999999)

# create table in database for assigning roles
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)