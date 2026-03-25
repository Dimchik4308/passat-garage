from datetime import datetime
from shared.database import db
from flask_login import UserMixin

class BotLogin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)

    user=db.relationship('User',foreign_keys=[user_id],backref='user_tgs')

    def __repr__(self):
        return f'<BotLogin {self.id}>'

class BotUser(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_telegram_id= db.Column(db.BigInteger,unique=True)

    def __repr__(self):
        return f'<BotUser {self.id}>'

class Good(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    descr= db.Column(db.Text,nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date=db.Column(db.DateTime, default=datetime.now)
    user_slug=db.Column(db.Integer, db.ForeignKey('user.slug'))
    slug=db.Column(db.String(255), unique=True , nullable=False)
    quantity=db.Column(db.Integer,  default=1, server_default='1', nullable=False)
    orders=db.Column(db.Integer,  default=1, server_default='1', nullable=False)
    town = db.Column(db.String(30), nullable=False)
    lower_title=db.Column(db.String(100), nullable=False)
    __table_args__=(
        db.CheckConstraint('price >= 0', name='price_positive'),
    )
    def __repr__(self):
        return f'<Good {self.id}>'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20), unique=True , nullable=False)
    email = db.Column(db.String(100), unique=True , nullable=False)
    password = db.Column(db.String(30), nullable=False)
    slug=db.Column(db.String(255),unique=True, nullable=False)
    goods=db.relationship('Good', backref='author', lazy= True)
    fname=db.Column(db.String(20), nullable=False)
    sname = db.Column(db.String(30), nullable=False)
    def __repr__(self):
        return f'<User {self.id}>'

class Order(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    fname=db.Column(db.String(20), nullable=False)
    sname = db.Column(db.String(30), nullable=False)
    quantity=db.Column(db.Integer,  default=1, server_default='1', nullable=False)
    town=db.Column(db.String(30), nullable=False)
    mail=db.Column(db.String(10), nullable=False)
    zip_code=db.Column(db.Integer, nullable=False)
    state=db.Column(db.String(10),default='waiting', server_default='waiting',nullable=False)
    comm=db.Column(db.Text,nullable=True)
    seller_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    buyer_id = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)
    good_id=db.Column(db.Integer,db.ForeignKey('good.id',ondelete='SET NULL'),nullable=True)
    fixed_title = db.Column(db.String(150), nullable=False)
    fixed_price = db.Column(db.Integer, nullable=False)
    fixed_img_url=db.Column(db.String(200), nullable=False)
    fixed_slug = db.Column(db.String(255), nullable=False)
    fixed_town=db.Column(db.String(30), nullable=True)
    date=db.Column(db.DateTime, default=datetime.now)
    buyer=db.relationship('User',foreign_keys=[buyer_id], backref='orders_bought')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='orders_selled')
    good=db.relationship('Good')
    total = db.Column(db.Integer, nullable=False)
    def __repr__(self):
        return f'<Order {self.id}>'
