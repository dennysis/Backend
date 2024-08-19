from flask import Flask, request, jsonify, session, make_response, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from config import app, db, api, login_manager
from models import Product, Category, User, Payment, SupplierProduct, SupplyRequest, Supplier, Transaction,SaleReturn,Sale,Purchase,Admin,Clerk,Inventory
from datetime import datetime,timedelta, timezone
from flask_jwt_extended import get_jwt_identity,get_jwt,jwt_required,set_access_cookies,create_access_token,unset_jwt_cookies
from config import app,mail
from flask_mail import Message
from sqlalchemy import func
from mpesa import mpesa_bp

app.register_blueprint(mpesa_bp, url_prefix='/m')

import os


@app.route('/')
def index():
    return '<h1>WELCOME !!</h1>'

@app.route('/signup', methods=['POST'])
def sign_up():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'User')

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 422

    if role not in ['Admin', 'User']:
        return jsonify({"error": "Invalid role"}), 422

    new_user = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        role=role
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Send confirmation email
        msg = Message('Welcome to Our Service!',
                      sender='inventract@gmail.com',
                      recipients=[email])
        msg.html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Inventrack</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background-color: #007bff;
            color: #ffffff;
            padding: 15px;
            border-radius: 8px 8px 0 0;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
        }}
        .content {{
            padding: 20px;
        }}
        .footer {{
            text-align: center;
            padding: 10px;
            font-size: 0.9em;
            color: #777;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Inventrack</h1>
        </div>
        <div class="content">
            <p>Hello {name},</p>
            <p>Thank you for signing up as a {role}. We are excited to have you on board!</p>
        </div>
        <div class="footer">
            <p>Best regards,</p>
            <p>The Inventrack Team</p>
        </div>
    </div>
</body>
</html>
'''
        mail.send(msg)
        message = "Admin created successfully" if role == 'Admin' else "User created successfully"
        return jsonify({"message": message}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already exists"}), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create user", "details": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

    login_user(user)
    response = jsonify({'success': True, 'message': 'Login successful'})
    access_token = create_access_token(identity=user.id)
    set_access_cookies(response, access_token)
    return response,200

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    response = jsonify({'success': True, 'message': 'Logout successful'})
    unset_jwt_cookies(response)
    logout_user()
    return response

@app.route('/checksession', methods=['GET'])
@jwt_required()
def check_session():
    user_id = get_jwt_identity()
    print(user_id)
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if user:
            return jsonify(user.to_dict()), 200
        else:
            return jsonify({"error": "User not found"}), 404
    else:
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/users/<int:user_id>', methods=['GET', 'PATCH'])
def manage_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if request.method == 'GET':
        return jsonify(user.to_dict())

    elif request.method == 'PATCH':
        data = request.get_json()
        role = data.get('role')

        if role is not None:
            user.role = role
            try:
                db.session.commit()
                return jsonify(user.to_dict()), 200
            except SQLAlchemyError as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 500

        return jsonify({"error": "Invalid data"}), 400

@app.route('/user', methods=['GET'])
@login_required
@jwt_required()
def user_details():
    user_id = current_user.id
    user = User.query.get(user_id)
    return make_response(jsonify(user.to_dict()), 200)

@app.route('/profile', methods=['GET'])
# @login_required
@jwt_required()
def profile():
    userId = get_jwt_identity()
    print(userId)
    try:
        user =User.query.filter_by(id=userId).first()
        transactions =user.transactions
        transaction_history = [transaction.to_dict() for transaction in transactions]
        activities = get_user_activities(userId)

        user_profile = {
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at,
            'transaction_history': transaction_history,
            'activities': activities
        }

        return jsonify(user_profile), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_user_activities(user_id):
    activities = [
        {'activity': 'Logged in', 'timestamp': datetime.utcnow()},
        {'activity': 'Made a purchase', 'timestamp': datetime.utcnow()},
    ]
    return activities

@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError

@app.route('/product/<int:product_id>', methods=['GET', 'PUT', 'DELETE'])
def product_detail(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if request.method == 'GET':
        return jsonify(product.to_dict())

    elif request.method == 'PUT':
        data = request.get_json()
        name = data.get('name')
        category_id = data.get('category_id')
        bp = data.get('bp')
        sp = data.get('sp')
        image_url = data.get('image_url')

        if name is not None:
            product.name = name
        if category_id is not None:
            product.category_id = category_id
        if bp is not None:
            product.bp = bp
        if sp is not None:
            product.sp = sp
        if image_url is not None:
            product.image_url = image_url  # Update the image URL

        try:
            db.session.commit()
            return jsonify(product.to_dict()), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            # Delete related purchases if necessary
            Purchase.query.filter_by(product_id=product_id).delete()

            db.session.delete(product)
            db.session.commit()
            return jsonify({'message': 'Product deleted successfully'}), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@app.route('/create_product', methods=['POST'])
def create_product():
    data = request.get_json()
    name = data.get('name')
    category_id = data.get('category_id')
    bp = data.get('bp')
    sp = data.get('sp')
    image_url = data.get('image_url')  

    if not all([name, category_id, bp, sp]):
        return jsonify({'error': 'Missing data'}), 400

    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404

    new_product = Product(
        name=name,
        category_id=category_id,
        bp=bp,
        sp=sp,
        image_url=image_url  
    )

    try:
        db.session.add(new_product)
        db.session.commit()
        return jsonify(new_product.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/payment', methods=['GET', 'POST'])
def manage_payment():
    if request.method == 'GET':
        payments = Payment.query.all()
        return jsonify([payment.to_dict() for payment in payments])

    elif request.method == 'POST':
        data = request.get_json()
        inventory_id = data.get('inventory_id')
        amount = data.get('amount')
        payment_date_str = data.get('payment_date')

        if inventory_id is None:
            return jsonify({'error': 'Missing inventory_id'}), 400
        if amount is None:
            return jsonify({'error': 'Missing amount'}), 400
        if payment_date_str is None:
            return jsonify({'error': 'Missing payment_date'}), 400

        try:
           
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid payment_date format'}), 400

        try:
            amount = float(amount)
        except ValueError:
            return jsonify({'error': 'Invalid amount format'}), 400
        
        payment = Payment(
            inventory_id=inventory_id,
            amount=amount,
            payment_date=payment_date
        )
        try:
            db.session.add(payment)
            db.session.commit()
            return jsonify({'message': 'Payment made successfully'}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@app.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories])

@app.route('/categories/<int:category_id>/products', methods=['GET'])
def get_products_by_category(category_id):
    products = Product.query.filter_by(category_id=category_id).all()
    return jsonify([product.to_dict() for product in products])


@app.route('/suppliers', methods=['GET'])
def get_suppliers():
    suppliers = Supplier.query.all()
    return jsonify([supplier.to_dict() for supplier in suppliers])
@app.route('/SupplierProduct', methods=['GET', 'POST'])
def get_supplier_products():
    if request.method == 'GET':
        
        supplier_products = SupplierProduct.query.all()
        return jsonify([sp.to_dict() for sp in supplier_products])
    
    elif request.method == 'POST':
        data = request.get_json()
        supplier_id = data.get('supplier_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        price = data.get('price')

        if supplier_id is None:
            return jsonify({'error': 'Missing supplier_id'}), 400
        if product_id is None:
            return jsonify({'error': 'Missing product_id'}), 400
        if quantity is None:
            return jsonify({'error': 'Missing quantity'}), 400
        if price is None:
            return jsonify({'error': 'Missing price'}), 400

        try:
            quantity = int(quantity)
            price = float(price)
        except ValueError:
            return jsonify({'error': 'Invalid quantity or price format'}), 400

        supplier_product = SupplierProduct(
            supplier_id=supplier_id,
            product_id=product_id,
            quantity=quantity,
            price=price
        )
        
        try:
            db.session.add(supplier_product)
            db.session.commit()
            return jsonify({'message': 'Supplier product added successfully'}), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
@app.route('/supplyrequests', methods=['GET', 'POST'])
def manage_supply_requests():
    if request.method == 'GET':
        supply_requests = SupplyRequest.query.all()
        return jsonify([request.to_dict() for request in supply_requests])

    if request.method == 'POST':
        data = request.get_json()
        new_request = SupplyRequest(
            product_id=data['product_id'],
            quantity=data['quantity'],
            clerk_id=data['clerk_id'],
            status=data['status']
        )
        db.session.add(new_request)
        db.session.commit()
        return jsonify(new_request.to_dict()), 201

@app.route('/supplyrequests/<int:supplyrequest_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_supply_request(supplyrequest_id):
    supply_request = SupplyRequest.query.get(supplyrequest_id)

    if not supply_request:
        return jsonify({'error': 'Supply request not found'}), 404

    if request.method == 'GET':
        return jsonify(supply_request.to_dict())

    if request.method == 'PUT':
        data = request.get_json()
        supply_request.product_id = data.get('product_id', supply_request.product_id)
        supply_request.quantity = data.get('quantity', supply_request.quantity)
        supply_request.clerk_id = data.get('clerk_id', supply_request.clerk_id)
        supply_request.status = data.get('status', supply_request.status)
        db.session.commit()
        return jsonify(supply_request.to_dict())

    if request.method == 'DELETE':
        db.session.delete(supply_request)
        db.session.commit()
        return jsonify({'message': 'Supply request deleted'})
    
@app.route('/complete_supply_request/<int:supplyrequest_id>', methods=['PUT'])
@login_required
def complete_supply_request(supplyrequest_id):
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403

    supply_request = SupplyRequest.query.get(supplyrequest_id)
    if not supply_request:
        return jsonify({'error': 'Supply request not found'}), 404

    supply_request.status = 'Completed'
    try:
        db.session.commit()
        return jsonify(supply_request.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@app.route('/product_sales', methods=['GET'])
def product_sales():
    try:
        
        product_sales = db.session.query(
            Product.name,
            db.func.sum(Sale.quantity).label('total_quantity')
        ).join(Sale, Product.id == Sale.product_id
        ).group_by(Product.id
        ).order_by(db.func.sum(Sale.quantity).desc()
        ).all()

        sales_data = [{'product': product.name, 'total_quantity': product.total_quantity} for product in product_sales]

        return jsonify(sales_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/total_revenue', methods=['GET'])
def total_revenue():
    try:
        
        total_revenue = db.session.query(
            db.func.sum(Sale.quantity * Sale.price).label('total_revenue')
        ).scalar()  

        return jsonify({
            'total_revenue': total_revenue if total_revenue is not None else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/total_sale_return', methods=['GET'])
def total_sale_return():
    try:
        total_return = db.session.query(
            db.func.sum(SaleReturn.quantity)
        ).scalar()
        
        return jsonify({'total_sale_return': total_return})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/total_purchase', methods=['GET'])
def total_purchase():
    try:
        total_purchase = db.session.query(
            db.func.sum(Purchase.price * Purchase.quantity)
        ).scalar()
        
        return jsonify({'total_purchase': total_purchase})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/total_income', methods=['GET'])
def total_income():
    try:
        total_income = db.session.query(
            db.func.sum(Sale.price * Sale.quantity) - db.func.sum(Purchase.price * Purchase.quantity)
        ).scalar()
        
        return jsonify({'total_income': total_income})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/best_seller_last_7_days', methods=['GET'])
def best_seller_last_7_days():
    try:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        best_seller = db.session.query(
            Product.name,
            db.func.sum(Sale.quantity).label('total_quantity')
        ).join(Sale, Product.id == Sale.product_id
        ).filter(Sale.sale_date >= seven_days_ago
        ).group_by(Product.id
        ).order_by(db.func.sum(Sale.quantity).desc()
        ).first()
        
        if best_seller:
            return jsonify({
                'product': best_seller.name,
                'total_quantity': best_seller.total_quantity
            })
        else:
            return jsonify({'error': 'No sales data available for the last 7 days'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/sales_data', methods=['GET'])
def sales_data():
    try:
        
        sales = db.session.query(
            Sale.sale_date.label('date'),
            db.func.sum(Sale.price).label('amount')
        ).group_by(Sale.sale_date).all()

        
        data = [{'date': sale.date.strftime('%Y-%m-%d'), 'amount': sale.amount} for sale in sales]

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/profit_loss_data', methods=['GET'])
def profit_loss_data():
    try:
        
        result = db.session.query(
            Sale.sale_date.label('date'),
            func.sum(Sale.price * Sale.quantity).label('amount')  
        ).group_by(Sale.sale_date).all()

        
        data = [{'date': sale.date.strftime('%Y-%m-%d'), 'amount': sale.amount} for sale in result]

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/clerk/login', methods=['POST'])
def clerk_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid email or password'}), 401

    if user.role != 'Clerk':
        return jsonify({'error': 'User is not a clerk'}), 403

    login_user(user)
    return jsonify({'message': 'Clerk login successful'}), 200

@app.route('/admin/clerk', methods=['POST'])
@login_required
def create_clerk():
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'All fields are required'}), 422

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 422

    new_clerk = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        role='Clerk'
    )

    try:
        db.session.add(new_clerk)
        db.session.commit()
        return jsonify({'message': 'Clerk created successfully'}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/clerks', methods=['GET'])
@login_required
def get_clerks():
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    clerks = User.query.filter_by(role='Clerk').all()
    return jsonify([clerk.to_dict() for clerk in clerks])

@app.route('/admin/clerks/<int:clerk_id>', methods=['PATCH', 'DELETE'])
@login_required
def manage_clerk(clerk_id):
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    clerk = User.query.get(clerk_id)
    if not clerk:
        return jsonify({'error': 'Clerk not found'}), 404

    if request.method == 'PATCH':
        data = request.get_json()
        role = data.get('role')

        if role and role == 'Clerk':
            clerk.role = role
            try:
                db.session.commit()
                return jsonify(clerk.to_dict()), 200
            except SQLAlchemyError as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 500

        return jsonify({'error': 'Invalid data'}), 400

    elif request.method == 'DELETE':
        try:
            db.session.delete(clerk)
            db.session.commit()
            return jsonify({'message': 'Clerk deleted successfully'}), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
        
@app.route('/admins/signup', methods=['POST'])
def signup_admin():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_admin = Admin(
        name=data['name'],
        email=data['email'],
        password=hashed_password
    )
    db.session.add(new_admin)
    db.session.commit()
    return jsonify(new_admin.to_dict()), 201

@app.route('/admins/login', methods=['POST'])
def login_admin():
    data = request.get_json()
    admin = Admin.query.filter_by(email=data['email']).first()
    
    if admin and check_password_hash(admin.password, data['password']):
       
        return jsonify(admin.to_dict()), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/admins', methods=['POST'])
def create_admin():
    data = request.get_json()
    new_admin = Admin(name=data['name'], email=data['email'], password=generate_password_hash(data['password'], method='sha256'))
    db.session.add(new_admin)
    db.session.commit()
    return jsonify(new_admin.to_dict()), 201

@app.route('/admins', methods=['GET'])
def get_admins():
    admins = Admin.query.all()
    return jsonify([admin.to_dict() for admin in admins])

@app.route('/admins/<int:id>', methods=['GET'])
def get_admin(id):
    admin = Admin.query.get_or_404(id)
    return jsonify(admin.to_dict())

@app.route('/admins/<int:id>', methods=['PUT'])
def update_admin(id):
    admin = Admin.query.get_or_404(id)
    data = request.get_json()
    admin.name = data['name']
    admin.email = data['email']
    admin.role = data['role']
    db.session.commit()
    return jsonify(admin.to_dict())

@app.route('/admins/<int:id>', methods=['DELETE'])
def delete_admin(id):
    admin = Admin.query.get_or_404(id)
    db.session.delete(admin)
    db.session.commit()
    return jsonify({'message': 'Admin deleted successfully'})
@app.route('/payment_status', methods=['GET'])
def get_payment_status():
    # Fetch inventory items with payment status
    inventory_items = Inventory.query.all()
    
    # Transform into a list of dictionaries
    payment_status = [
        {
            'id': item.id,
            'product_id': item.product_id,
            'quantity': item.quantity,
            'spoilt_quantity': item.spoilt_quantity,
            'payment_status': item.payment_status,
            'created_at': item.created_at.isoformat()
        }
        for item in inventory_items
    ]
    
    return jsonify(payment_status)

if __name__ == '__main__':
   
    app.run(debug=True)