from datetime import datetime
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Numeric, DateTime
from config import db
from flask_login import UserMixin
from sqlalchemy.orm import backref, relationship

class Transaction(db.Model, SerializerMixin):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    inventory_id = db.Column(db.Integer, ForeignKey('inventory.id'), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='transactions')
    inventory = db.relationship('Inventory', back_populates='transactions')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "inventory_id": self.inventory_id,
            "transaction_type": self.transaction_type,
            "quantity": self.quantity,
            "created_at": self.created_at,
        }

class Product(db.Model, SerializerMixin):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    bp = db.Column(db.Float, nullable=False)
    sp = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String, nullable=True)
    
    category = db.relationship('Category', back_populates='products')
    inventory_items = db.relationship('Inventory', back_populates='product', cascade='all, delete-orphan')
    product_sales = db.relationship('Sale', back_populates='product')
    purchases = db.relationship('Purchase', back_populates='product', cascade='all, delete-orphan')  
    supplier_products = db.relationship('SupplierProduct', back_populates='product', cascade='all, delete-orphan')  
    
    serialize_rules = ('-inventory_items.product',)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category_id': self.category_id,
            'bp': self.bp,
            'sp': self.sp,
            "image": self.image_url
        }

class Inventory(db.Model, SerializerMixin):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    spoilt_quantity = db.Column(db.Integer, nullable=False, default=0)
    payment_status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    product = db.relationship('Product', back_populates='inventory_items')
    transactions = db.relationship('Transaction', back_populates='inventory', lazy=True)

class User(db.Model, UserMixin, SerializerMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', back_populates='user')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at
        }

class Clerk(User):
    __tablename__ = 'clerks'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    user = db.relationship('User', backref=db.backref('clerk', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': 'Clerk',
            'created_at': self.created_at
        }

class Admin(db.Model, UserMixin, SerializerMixin):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at
        }

class Category(db.Model, SerializerMixin):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(200), nullable=True)

    products = db.relationship('Product', back_populates='category')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }

class Supplier(db.Model, SerializerMixin):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.Text, nullable=False)

    supplier_products = db.relationship('SupplierProduct', back_populates='supplier')

class SupplyRequest(db.Model):
    __tablename__ = 'supply_requests'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    clerk_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'clerk_id': self.clerk_id,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class Payment(db.Model, SerializerMixin):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    amount = db.Column(db.Numeric, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'inventory_id': self.inventory_id,
            'amount': str(self.amount),
            'payment_date': self.payment_date.strftime('%Y-%m-%d')
        }

class SupplierProduct(db.Model, SerializerMixin):
    __tablename__ = 'supplier_products'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, ForeignKey('suppliers.id'), nullable=False)
    product_id = db.Column(db.Integer, ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    supplier = db.relationship('Supplier', back_populates='supplier_products')
    product = db.relationship('Product', back_populates='supplier_products')

class ProductCategory(db.Model):
    __tablename__ = 'product_categories'
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref=backref('product_categories', cascade='all, delete-orphan'))
    category = db.relationship('Category', backref=backref('product_categories', cascade='all, delete-orphan'))

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, ForeignKey('products.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', back_populates='product_sales')
    returns = db.relationship('SaleReturn', back_populates='sale')

class SaleReturn(db.Model):
    __tablename__ = 'sale_returns'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, ForeignKey('sales.id'))
    quantity = db.Column(db.Integer)
    return_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    sale = db.relationship('Sale', back_populates='returns')

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', back_populates='purchases')
