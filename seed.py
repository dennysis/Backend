import requests
from app import app
from config import db
from models import (Product, Category, User, Inventory, Transaction, Supplier, 
                    SupplyRequest, Payment, SupplierProduct, Sale, SaleReturn, Purchase)
from faker import Faker
from sqlalchemy.exc import IntegrityError
import random

fake = Faker()

def fetch_data(url, limit=None):
    """Fetches data from the provided URL and applies a limit if specified."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if limit:
            data = data[:limit]
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data from {url}: {e}")
        return []

def seed_categories():
    """Seeds the Category table using data from a fake store API."""
    categories = fetch_data('https://fakestoreapi.com/products/categories')
    for category in categories:
        if category and category != "Testing Category":
            existing_category = Category.query.filter_by(name=category).first()
            if not existing_category:
                new_category = Category(
                    name=category,
                    description=f"{category} category"
                )
                db.session.add(new_category)
    db.session.commit()
    print(f"Seeded {len(categories)} categories (excluding 'Testing Category').")

def seed_products(limit=20):
    """Seeds the Product table using data from a fake store API and Faker."""
    # Fetch products from API
    products = fetch_data('https://fakestoreapi.com/products')
    seeded_count = 0

    # Seed products from API data
    for product in products:
        if seeded_count >= limit:
            break
        if product:
            existing_product = Product.query.filter_by(name=product['title']).first()
            if not existing_product:
                category = Category.query.filter_by(name=product["category"]).first()
                if category:
                    new_product = Product(
                        name=product['title'],
                        category_id=category.id,
                        bp=float(product['price']) * 0.8,
                        sp=float(product['price']),
                        image_url=f"https://via.placeholder.com/150x150?text={product['title'].replace(' ', '+')}"
                    )
                    db.session.add(new_product)
                    seeded_count += 1

    # Generate additional products using Faker if needed
    max_category_id = db.session.query(db.func.max(Category.id)).scalar()
    while seeded_count < limit:
        new_product = Product(
            name=fake.word(),
            category_id=random.randint(1, max_category_id) if max_category_id else 1,
            bp=random.uniform(5.0, 50.0),
            sp=random.uniform(50.0, 100.0),
            image_url=f"https://via.placeholder.com/150x150?text={fake.word().replace(' ', '+')}"
        )
        db.session.add(new_product)
        seeded_count += 1

    db.session.commit()
    print(f"Seeded {seeded_count} products.")


def seed_users():
    """Seeds the User table using data from a fake user API."""
    users = fetch_data('https://api.escuelajs.co/api/v1/users')
    for user in users:
        if user:
            existing_user = User.query.filter_by(email=user['email']).first()
            if not existing_user:
                new_user = User(
                    name=user['name'],
                    email=user['email'],
                    password=user['password'],  # Ensure secure password handling
                    role=user.get("role", "user")
                )
                db.session.add(new_user)
    db.session.commit()
    print(f"Seeded {len(users)} users.")

def seed_inventory(limit=20):
    """Seeds the Inventory table with random data."""
    # Fetch all product IDs from the products table
    product_ids = [product.id for product in Product.query.all()]

    if not product_ids:
        print("No products available to seed inventory.")
        return

    for i in range(limit):
        new_inventory = Inventory(
            product_id=random.choice(product_ids),  # Ensure the product_id is valid
            quantity=random.randint(10, 100),
            spoilt_quantity=random.randint(0, 10),
            payment_status=random.choice(['Paid', 'Pending', 'Overdue'])
        )
        db.session.add(new_inventory)
    
    db.session.commit()
    print(f"Seeded {limit} inventory items.")

def seed_transactions(limit=20):
    """Seeds the Transaction table with random data."""
    inventory_ids = [inventory.id for inventory in Inventory.query.all()]
    if not inventory_ids:
        print("No inventory available to seed transactions.")
        return

    user_ids = [user.id for user in User.query.all()]
    if not user_ids:
        print("No users available to seed transactions.")
        return

    for i in range(limit):
        new_transaction = Transaction(
            user_id=random.choice(user_ids),
            inventory_id=random.choice(inventory_ids),
            transaction_type=random.choice(['sale', 'purchase', 'return']),
            quantity=random.randint(1, 10)
        )
        db.session.add(new_transaction)
    db.session.commit()
    print(f"Seeded {limit} transactions.")

def seed_suppliers(limit=20):
    """Seeds the Supplier table with random data."""
    for i in range(limit):
        new_supplier = Supplier(
            name=fake.company(),
            contact_info=fake.address()
        )
        db.session.add(new_supplier)
    db.session.commit()
    print(f"Seeded {limit} suppliers.")

def seed_supply_requests(limit=20):
    """Seeds the SupplyRequest table with random data."""
    for i in range(limit):
        product_ids = [product.id for product in Product.query.all()]
        

        new_supply_request = SupplyRequest(
            product_id=random.choice(product_ids),
            quantity=random.randint(10, 100),
            clerk_id=random.randint(1, limit),
            status=random.choice(['pending', 'approved', 'rejected'])
        )
        db.session.add(new_supply_request)
    db.session.commit()
    print(f"Seeded {limit} supply requests.")

def seed_payments(limit=20):
    """Seeds the Payment table with random data."""
    for i in range(limit):
        inventory_ids = [inventory.id for inventory in Inventory.query.all()]
        new_payment = Payment(
            inventory_id=random.choice(inventory_ids),
            amount=random.uniform(50.0, 500.0)
        )
        db.session.add(new_payment)
    db.session.commit()
    print(f"Seeded {limit} payments.")

def seed_supplier_products(limit=20):
    """Seeds the SupplierProduct table with random data."""
    for i in range(limit):
        supplier_ids = [supplier.id for supplier in Supplier.query.all()]
        product_ids = [product.id for product in Product.query.all()]
        new_supplier_product = SupplierProduct(
            supplier_id=random.choice(supplier_ids),
            product_id=random.choice(product_ids),
            quantity=random.randint(10, 100),
            price=random.uniform(10.0, 100.0)
        )
        db.session.add(new_supplier_product)
    db.session.commit()
    print(f"Seeded {limit} supplier products.")

def seed_sales(limit=20):
    """Seeds the Sale table with random data."""
    for i in range(limit):
        product_ids = [product.id for product in Product.query.all()]
        new_sale = Sale(
            product_id=random.choice(product_ids),
            quantity=random.randint(1, 10),
            price=random.uniform(20.0, 200.0)
        )
        db.session.add(new_sale)
    db.session.commit()
    print(f"Seeded {limit} sales.")

def seed_sale_returns(limit=20):
    """Seeds the SaleReturn table with random data."""
    for i in range(limit):
        sale_ids = [sale.id for sale in Sale.query.all()]
        new_sale_return = SaleReturn(
            sale_id=random.choice(sale_ids),
            quantity=random.randint(1, 5)
        )
        db.session.add(new_sale_return)
    db.session.commit()
    print(f"Seeded {limit} sale returns.")

def seed_purchases(limit=20):
    """Seeds the Purchase table with random data."""
    for i in range(limit):
        product_ids = [product.id for product in Product.query.all()]
        new_purchase = Purchase(
            product_id=random.choice(product_ids),
            quantity=random.randint(1, 10),
            price=random.uniform(20.0, 200.0)
        )
        db.session.add(new_purchase)
    db.session.commit()
    print(f"Seeded {limit} purchases.")

def seed_all():
    """Seeds all tables with initial data."""
    seed_categories()
    seed_products(limit=20)
    seed_users()
    seed_inventory(limit=20)
    seed_transactions(limit=20)
    seed_suppliers(limit=20)
    seed_supply_requests(limit=20)
    seed_payments(limit=20)
    seed_supplier_products(limit=20)
    seed_sales(limit=20)
    seed_sale_returns(limit=20)
    seed_purchases(limit=20)

if __name__ == "__main__":
    with app.app_context():
        seed_all()
