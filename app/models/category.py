from app.extensions import db

#class DB
class Category(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    Name = db.Column(db.String, nullable=False)
    
   

    def _repr_(self):
        return f'<Category "{self.category_name}">'