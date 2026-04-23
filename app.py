from flask_login import  login_user, LoginManager, login_required, logout_user, current_user
from flask import Flask,render_template,request,redirect, url_for,abort,flash
from werkzeug.utils import secure_filename
from slugify import slugify
from werkzeug.security import generate_password_hash,check_password_hash
from shared.database import db
from shared.models import Good,Order,User
from flask_migrate import Migrate
import requests
from random import randint
import time
import os
from dotenv import load_dotenv
import redis

app = Flask(__name__)

load_dotenv()

app.config['SECRET_KEY']=os.getenv("FLASK_SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"]=os.getenv('FLASK_DATABASE_URL')
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

migrate=Migrate(app,db)
db.init_app(app)

login_manager=LoginManager(app)
login_manager.login_view = 'signin'

r = redis.Redis(
    host=os.getenv('REDIS_HOST', '127.0.0.1'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=True
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/aboutus')
def about():
    return render_template('about.html')

@app.route('/telegram')
def link_tg():
    def generate_random_code():
        while True:
            code = str(randint(0, 999999)).zfill(6)
            if not r.exists(f"auth_code:{code}"):
                return code
    user_id = current_user.id 
    auth_code = generate_random_code() 
    r.set(f"auth_code:{auth_code}", user_id, ex=300)

    return render_template('tg.html', code=auth_code)

@app.route('/search')
def search():
    q=request.args.get('q')
    if q:
        goods=Good.query.filter(Good.lower_title.ilike(f'%{q.lower()}%')).all()
        return render_template('search.html',goods=goods,q=q)
    else:
        goods = Good.query.order_by(Good.orders.desc()).all()
        return render_template("index.html", goods=goods)


@app.route('/search<string:category>')
def search_category(category):
    qc = request.args.get('qc')
    if qc:
        goods = Good.query.filter(Good.lower_title.ilike(f'%{qc.lower()}%'),Good.category==category).all()
        return render_template('search_category.html', goods=goods, qc=qc)
    else:
        goods = Good.query.where(Good.category == category).all()
        return render_template('category.html', goods=goods, category_name=category)


@app.route('/<int:id>/orderdetail')
@login_required
def order_detail(id):
    order=Order.query.get(id)
    return render_template('order_detail.html',order=order)

@app.route('/myorders')
@login_required
def my_orders():
    orders = Order.query.filter_by(seller_id=current_user.id).all()
    buy_orders = Order.query.filter_by(buyer_id=current_user.id).all()
    return render_template('orders.html',orders=orders,buy_orders=buy_orders)

@app.route('/set/<string:status>/<int:id>')
@login_required
def set_status(status,id):
    ids = [i[0] for i in db.session.query(Order.id).all()]
    if status=='waiting' or status=='denied' or status=='inprocess' or status=='finished' and id in ids:
        order = Order.query.get(id)
        order.state = status
        bot_api_url = os.getenv('FASTAPI_URL')

        payload = {
            "code": str(status),
            "title": str(order.fixed_title),
            "seller_id": int(order.seller_id),
            "buyer_id": int(order.buyer_id),
            "seller_email":str(order.seller.email),
            "buyer_email": str(order.buyer.email),
            "seller_name":str(order.seller.username),
            "buyer_name": str(order.buyer.username)
        }

        try:
            headers = {"X-Internal-Key": os.getenv("INTERNAL_API_KEY")}
            response = requests.post(f'{bot_api_url}/order_status', json=payload,headers=headers)
        except requests.exceptions.RequestException as e:
            return f'Виникла помилка'

    else:
        abort(403)
    try:
        db.session.commit()
        return redirect(url_for('my_orders'))
    except:
        return f'При встановленні статусу відбулася помилка'


@app.route('/myorders/waiting')
@login_required
def waiting_orders():
    orders=Order.query.filter(Order.state=='waiting',Order.seller_id==current_user.id).all()
    buy_orders = Order.query.filter(Order.state == 'waiting', Order.buyer_id == current_user.id).all()
    return render_template('order_category.html',orders=orders,buy_orders=buy_orders,status='Очікують на підтверження')

@app.route('/myorders/denied')
@login_required
def denied_orders():
    orders = Order.query.filter(Order.state == 'denied', Order.seller_id == current_user.id).all()
    buy_orders = Order.query.filter(Order.state == 'denied', Order.buyer_id == current_user.id).all()
    return render_template('order_category.html', orders=orders, buy_orders=buy_orders,status='Відхиленні')
@app.route('/myorders/inprocess')
@login_required
def inprocess_orders():
    orders = Order.query.filter(Order.state == 'inprocess', Order.seller_id == current_user.id).all()
    buy_orders = Order.query.filter(Order.state == 'inprocess', Order.buyer_id == current_user.id).all()
    return render_template('order_category.html', orders=orders, buy_orders=buy_orders,status='В обробці')
@app.route('/myorders/finished')
@login_required
def finished_orders():
    orders = Order.query.filter(Order.state == 'finished', Order.seller_id == current_user.id).all()
    buy_orders = Order.query.filter(Order.state == 'finished', Order.buyer_id == current_user.id).all()
    return render_template('order_category.html', orders=orders, buy_orders=buy_orders,status='Завершені')

@app.route('/catalog/<string:slug>/buy',methods=['POST','GET'])
@login_required
def buy_good(slug):
    good=Good.query.filter_by(slug=slug).first_or_404()
    if good.quantity==0 or current_user==good.author:
        abort(403)
    if request.method=='POST':
        fname=request.form['fname']
        sname = request.form['sname']
        quantity=request.form['quantity']
        town=request.form['town']
        mail=request.form['mail']
        zip_code=request.form['index']
        comm=request.form['com']
        if fname and sname and quantity and town and mail and zip_code :
            if int(quantity)<1 :
                flash('Ви не можете замовити менше одного товару', 'error')
                return render_template('buy_good.html')
            if int(quantity) > good.quantity:
                flash('Стільки товарів немає в наявності', 'error')
                return render_template('buy_good.html')
            total = int(good.price) * int(quantity)
            order=Order(fname=fname,sname=sname,quantity=quantity,town=town,mail=mail,zip_code=zip_code,comm=comm,
                         seller_id=good.author.id,buyer_id=current_user.id,good_id=good.id,fixed_title=good.title,
                         fixed_price=good.price,fixed_img_url=good.image_url,fixed_slug=good.slug,total=total)
            bot_api_url = os.getenv('FASTAPI_URL')

            payload = {
                "fname":str(fname),
                "sname": str(sname),
                "quantity": int(quantity),
                "town": str(town),
                "mail":str(mail),
                "zip_code":str(zip_code),
                "comment":str(comm),
                "seller_id":str(good.author.id),
                "good_title":str(good.title),
                "total":int(total),
                "email":str(current_user.email)
            }

            try:
                headers = {"X-Internal-Key": os.getenv("INTERNAL_API_KEY")}
                response = requests.post(f'{bot_api_url}/order_not', json=payload,headers=headers)
            except requests.exceptions.RequestException as e:
                return f'Виникла помилка '
            try:
                good.quantity -= int(quantity)
                good.orders += 1
                db.session.add(order)
                db.session.commit()
                flash('Ви успішно замовили товар', 'success')
                return redirect(url_for('my_orders'))
            except:
                flash('При замовленні відбулася помилка. Спробуйте ще раз.', 'error')
                return render_template('buy_good.html')
        else:
            abort(403)
    else:
        return render_template('buy_good.html',good=good)
@app.route('/')
def main_page():
    goods = Good.query.order_by(Good.orders.desc()).all()
    return render_template("index.html",goods=goods)

@app.route('/catalog')
def catalog():
    goods=Good.query.order_by(Good.date.desc()).all()
    return render_template("catalog.html",goods=goods)

@app.route('/catalog/<string:slug>')
def good_detail(slug):
    good=Good.query.filter_by(slug=slug).first_or_404()
    similar_goods=Good.query.filter(Good.category==good.category ,Good.id!=good.id).order_by(Good.orders.desc()).limit(7)
    return render_template("good_detail.html",good=good,similar_goods=similar_goods)

@app.route('/my_goods')
@login_required
def user_good():
    goods=current_user.goods
    return render_template('user_goods.html',goods=goods)

@app.route('/catalog/<string:slug>/del')
@login_required
def good_delete(slug):
    good=Good.query.filter_by(slug=slug).first_or_404()
    if current_user.id != good.author.id:
        abort(403)
    try:
        os.remove(good.image_url)
        db.session.delete(good)
        db.session.commit()
        return redirect(url_for('catalog'))
    except:
        flash('При видаленні товару відбулася помилка', 'error')
        return render_template('catalog.html')

@app.route('/catalog/<string:slug>/update',methods=['POST','GET'])
@login_required
def good_update(slug):
    good=Good.query.filter_by(slug=slug).first_or_404()
    if current_user.id != good.author.id:
        abort(403)
    if request.method == 'POST':
        good.title=request.form['title']
        good.price = request.form['price']
        good.descr = request.form['descr']
        good.category=request.form['category']
        good.file=request.files['imageFile']
        good.quantity = request.form['quantity']
        if int(good.quantity)<0:
            flash('Кількість товарів має бути більшою, ніж нуль', 'error')
            return render_template('good_update.html')
        if 'imageFile' in request.files:
            file=request.files['imageFile']
            if file and file.filename != '':
                end = file.filename.index('.')
                final = secure_filename(f'{file.filename[0:end]}{int(time.time())}{file.filename[end:len(file.filename)]}')
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], final))
                good.image_url = f'static/uploads/{final}'
        try:
            db.session.commit()
            return redirect(url_for('catalog'))
        except:
            flash('Відбулася помилка при оновленні даних товару. Спробуйте ще раз', 'error')
            return render_template('good_update.html')
    else:
        return render_template("good_update.html",good=good)

@app.route('/liquids')
def liquids():
    goods=Good.query.where(Good.category=='💧 Мастила та рідини').all()
    return render_template('category.html', goods=goods, category_name='💧 Мастила та рідини')
@app.route('/running')
def running():
    goods=Good.query.where(Good.category=='🚗 Ходова частина').all()
    return render_template('category.html', goods=goods,category_name='🚗 Ходова частина')

@app.route('/engine')
def engine():
    goods=Good.query.where(Good.category=='🔧 Двигун та вихлоп').all()
    return render_template('category.html', goods=goods,category_name='🔧 Двигун та вихлоп')

@app.route('/brakes')
def brakes():
    goods=Good.query.where(Good.category=='🛑 Гальмівна система').all()
    return render_template('category.html', goods=goods,category_name='🛑 Гальмівна система')

@app.route('/electric')
def electric():
    goods=Good.query.where(Good.category=='⚡ Електрика та світло').all()
    return render_template('category.html', goods=goods,category_name='⚡ Електрика та світло')

@app.route('/other')
def other():
    goods=Good.query.where(Good.category=='✨ Інше').all()
    return render_template('category.html', goods=goods,category_name='✨ Інше')

@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        fname=request.form['fname']
        sname=request.form['sname']
        if username and email and password and fname and sname:
            ffname = fname[0].upper() + fname[1:len(fname)]
            fsname = sname[0].upper() + sname[1:len(sname)]
            slug_str = slugify(username)
            if Good.query.filter_by(slug=slug_str).first():

                slug_str = f'{slug_str}-{int(time.time())}'
            if len(password)<8:
                flash('Пароль має складатися мінімум з 8 символів','error')
                return render_template('register.html')
            elif password.islower():
                flash('Пароль має містити великі букви', 'error')
                return render_template('register.html')
            elif '@' and '.' not in email:
                flash('Ви ввели невалідну адресу електронної пошти', 'error')
                return render_template('register.html')
            elif password.isalpha():
                flash('Пароль має містити цифри', 'error')
                return render_template('register.html')
            elif password.isdigit():
                flash('Пароль має містити букви', 'error')
                return render_template('register.html')
            else:
                hashed_pass=generate_password_hash(password,method='scrypt')
            user=User(username=username,email=email,password=hashed_pass,slug=slug_str,fname=ffname,sname=fsname)
            try:
                db.session.add(user)
                db.session.commit()
                flash('Ви успішно зареєструвалися', 'success')
                return redirect(url_for('signin'))
            except :
                flash('При реєстрації відбулася помилка. Ми вже працюємо над цим', 'error')
                return render_template('register.html')
        else:
            abort(403)
    else:
        return render_template('register.html')
@app.route('/signin',methods=['POST','GET'])
def signin():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        user=User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password,password):
            login_user(user)
            return redirect(url_for('main_page'))
        else:
            flash('Ви ввели неправильний пароль або логін', 'error')
            return render_template('login.html')
    else:
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main_page'))
@app.route('/add',methods=['POST','GET'])
@login_required
def add_good():
    if request.method == 'POST':
        title=request.form['title']
        price = request.form['price']
        descr = request.form['descr']
        category=request.form['category']
        file=request.files['imageFile']
        slug_str=slugify(title)
        quantity=request.form['quantity']
        town=request.form['town']
        if title and price and descr and category and file and slug_str and quantity and town:
            lower_title=title.lower()
            if int(price)<0:
                flash("Ціна не може бути від'ємною", 'error')
                return render_template('add_good.html')
            if int(quantity)<=0:
                flash("Ви маєте продавати хоча б один товар", 'error')
                return render_template('add_good.html')
            if Good.query.filter_by(slug=slug_str).first():
                slug_str=f'{slug_str}-{int(time.time())}'
            if file.filename != '':
                end = file.filename.index('.')
                final = secure_filename(f'{file.filename[0:end]}{int(time.time())}{file.filename[end:len(file.filename)]}')
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], final))
                image_url=f'static/uploads/{final}'
            good=Good(title=title,price=price,descr=descr,category=category,image_url=image_url,author=current_user,slug=slug_str,quantity=quantity,town=town,lower_title=lower_title)
            bot_api_url = os.getenv("FASTAPI_URL")
            payload = {
                "img_url":str(image_url),
                "title": str(title),
                "price": int(price),
                "slug": str(slug_str),
                "seller":str(current_user.username)
            }

            try:
                headers = {"X-Internal-Key": os.getenv("INTERNAL_API_KEY")}
                response = requests.post(f'{bot_api_url}/notify', json=payload,headers=headers)
            except requests.exceptions.RequestException as e:
                return f'Виникла помилка {e}'
            try:
                db.session.add(good)
                db.session.commit()

                return redirect(url_for('catalog'))
            except:
                flash("При додаванні товару відбулася помилка. Спробуйте ще раз", 'error')
                return render_template('add_good.html')

        else:
            abort(403)
    else:
        return render_template("add_good.html")

if __name__ == '__main__':
    app.run(debug=True)
