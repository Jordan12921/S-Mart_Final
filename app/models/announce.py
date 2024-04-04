from app.extensions import db


class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Content {self.id}>'