from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///appdatabase.sqlite3"
app.debug = True
db = SQLAlchemy(app)
app.app_context().push()

class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String, nullable=False)
    products = db.relationship("Product", back_populates="category")

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String, nullable=False)
    manufacturing_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    rate = db.Column(db.Integer)
    unit = db.Column(db.String)
    available_quantity = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey("category.category_id"))
    category = db.relationship("Category", back_populates="products")

class Admin(db.Model):
    admin_id = db.Column(db.String, primary_key=True)
    admin_password = db.Column(db.String, nullable=False)

class User(db.Model):
    user_id = db.Column(db.String, primary_key=True)
    user_password = db.Column(db.String, nullable=False)

@app.route('/', methods=['GET', 'POST'])
def user():
  if request.method == 'POST':
    u_username = request.form['u_username']
    u_password = request.form['u_password']

    user = User(
        user_id = u_username,
        user_password = u_password
    )

    db.session.add(user)
    db.session.commit()
    return redirect('/grocery/store')
  return render_template('user.html')

@app.route('/grocery/store', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('query', '')
        filter_option = request.form.get('filter', 'product_name')

        if filter_option == 'product_name':
            products = Product.query.filter(Product.product_name.ilike(f'%{query}%')).all()
        elif filter_option == 'category_name':
            category = Category.query.filter(Category.category_name.ilike(f'%{query}%')).first()
            if category:
                products = category.products
            else:
                products = []
        elif filter_option == 'expiry_date':
            expiry_date_str = request.form.get('query')
            if expiry_date_str:
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
                products = Product.query.filter(Product.expiry_date > expiry_date).all()
            else:
                products = []
        elif filter_option == 'price':
            max_price_str = request.form.get('query')
            if max_price_str:
                max_price = float(max_price_str)
                products = Product.query.filter(Product.rate < max_price).all()
            else:
                products = []
        else:
            products = []

        categories = Category.query.all()
        return render_template('search_results.html', categories=categories, products=products, filter_option=filter_option)

    categories = Category.query.all()
    return render_template('search_results.html', categories=categories)

cart_items = []

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_name = request.form.get('product_name')
    price = float(request.form.get('price'))
    quantity = int(request.form.get('quantity'))
    if quantity > 0:
        item = {
            'product_name': product_name,
            'price': price,
            'quantity': quantity
        }
        cart_items.append(item)
        product = Product.query.filter_by(product_name=product_name).first()
        if product:
            if product.available_quantity >= quantity:
                product.available_quantity -= quantity
                db.session.commit()
            else:
                return f"Insufficient quantity for {product_name}."
        else:
            return f"Product {product_name} not found."

    return redirect('/cart')

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_name = request.form.get('product_name')
    for item in cart_items:
        if item['product_name'] == product_name:
            quantity = item['quantity']
            if quantity > 0:
                item['quantity'] -= 1
                if item['quantity'] == 0:
                    cart_items.remove(item)
                    product = Product.query.filter_by(product_name=product_name).first()
                    if product:
                        product.available_quantity += 1
                        db.session.commit()
                    break
    return redirect('/cart')

@app.route('/static/js/cart.js')
def cart_js():
    return app.send_static_file('js/cart.js')

@app.route('/cart', methods=['POST', 'GET'])
def cart():
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    if request.method == 'POST':
        for item in cart_items:
            product_name = item['product_name']
            quantity = item['quantity']
            if quantity > 0:
                product = Product.query.filter_by(product_name=product_name).first()
                print(product)
                if product:
                    if product.available_quantity >= quantity:
                        product.available_quantity -= quantity
                    else:
                        return f"Insufficient quantity for {product_name}."
                    print(product.available_quantity)
                else:
                    return f"Product {product_name} not found."
        db.session.commit()
        cart_items.clear()
        return redirect('/endpage')
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/endpage', methods=['GET', 'POST'])
def endpage():
    if request.method == 'POST':
        for item in cart_items:
            product_name = item['product_name']
            quantity = item['quantity']
            if quantity > 0:
                product = Product.query.filter_by(product_name=product_name).first()
                if product:
                    if product.available_quantity >= quantity:
                        product.available_quantity -= quantity
                        db.session.commit()
                    else:
                        return f"Insufficient quantity for {product_name}."
                else:
                    return f"Product {product_name} not found."
        cart_items.clear()
        return redirect('/endpage')
    return render_template('endpage.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        a_username = request.form['a_username']
        a_password = request.form['a_password']

        admin = Admin(
            admin_id=a_username,
            admin_password=a_password
        )

        db.session.add(admin)
        db.session.commit()
        return redirect('/management')
    return render_template('admin.html')

@app.route('/management')
def manage():
    return render_template('manage.html')

@app.route('/inventory')
def inventory_management():
    return render_template('inventory.html')

@app.route('/product')
def product():
    return render_template('product.html')

@app.route('/category/create', methods=['POST', 'GET'])
def create_category():
    if request.method == 'POST':
        c_name = request.form['c_name']

        cat = Category(
            category_name=c_name
        )
        db.session.add(cat)
        db.session.commit()

        return redirect('/categories')
    return render_template("create_category.html")  

@app.route('/category/edit', methods=['GET', 'POST'])
def edit_category():
    if request.method == 'POST':
        old_category_name = request.form['old_category_name']
        new_category_name = request.form['new_category_name']
        category = Category.query.filter_by(category_name=old_category_name).first()
        if category:
            category.category_name = new_category_name
            db.session.commit()
        else:
            return "Category Not Found"
        return redirect('/categories')
    categories = Category.query.all()
    return render_template('edit_category.html', categories=categories)

@app.route('/categories')
def view_categories():
    all_categories = Category.query.all()
    return render_template("view_categories.html", all_categories=all_categories)

@app.route('/category/remove', methods=['POST', 'GET'])
def remove_category():
    if request.method == 'POST':
        c_name = request.form['c_name']
        category = Category.query.filter_by(category_name=c_name).first()
        if category:
            db.session.delete(category)
            db.session.commit()
        else:
            return "Category not found."
        return redirect('/categories')
    return render_template("remove_category.html")

@app.route('/product/create', methods=['POST', 'GET'])
def create_product():
    if request.method == 'POST':
        p_name = request.form['p_name']
        m_date = datetime.strptime(request.form['m_date'], '%Y-%m-%d').date()
        e_date = datetime.strptime(request.form['e_date'], '%Y-%m-%d').date()
        rate = float(request.form['rate'])
        unit = request.form['unit']
        quantity = int(request.form['quantity'])
        category_id = int(request.form['category'])

        prod = Product(
            product_name=p_name,
            manufacturing_date=m_date,
            expiry_date=e_date,
            rate=rate,
            unit=unit,
            available_quantity=quantity,
            category_id=category_id,
        )
        db.session.add(prod)
        db.session.commit()

        all_products = Product.query.order_by(Product.category_id).all()
        categories = Category.query.all()

        return render_template("view_products.html", all_products=all_products, categories=categories)

    cats = Category.query.all()
    return render_template("create_product.html", cats=cats)

@app.route('/product/edit', methods=['POST', 'GET'])
def edit_product():
    if request.method == 'POST':
        product_name = request.form['p_name']
        new_rate = request.form['new_rate']
        new_quantity = request.form['new_quantity']
        product = Product.query.filter_by(product_name=product_name).first()
        if product is None:
            return "Product not found"
        product.rate = new_rate
        product.available_quantity = new_quantity
        db.session.commit()
        return redirect('/products')
    return render_template('edit_product.html')

@app.route('/products')
def view_products():
    all_products = Product.query.order_by(Product.category_id).all()
    categories = Category.query.all()
    return render_template("view_products.html", all_products=all_products, categories=categories)

@app.route('/product/remove', methods=['POST', 'GET'])
def remove_product():
    if request.method == 'POST':
        p_name = request.form['p_name']
        product = Product.query.filter_by(product_name=p_name).first()
        if product:
            db.session.delete(product)
            db.session.commit()
        else:
            return "Product not found."
        return redirect('/products')
    return render_template("remove_product.html")  

if __name__ == '__main__':
    app.run(debug=True)
