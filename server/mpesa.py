import requests
from requests.auth import HTTPBasicAuth
from flask import Blueprint, jsonify, request
from decimal import Decimal, InvalidOperation
from config import db
from models import User, Payment

mpesa_bp = Blueprint('mpesa', __name__)

# Safaricom credentials (sandbox)
consumer_key = 'MYGtWYL0FIXO1BTdBiA6dXDiOUfSviRAalexLtiEAiIPKhMJ'
consumer_secret = 'FJxVc5tcQIKMmDREIcnUo5T60zXoGnGJwGPhbV5J5oO3LEQEnLxKMPj8mvV36BK6'

def generate_access_token(consumer_key, consumer_secret):
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    json_response = response.json()
    access_token = json_response['access_token']
    return access_token

def get_user_by_phone(phone_number):
    user = User.query.filter_by(phone_number=phone_number).first()
    if user:
        return {
            'id': user.id,
            'phone_number': user.phone_number,
            'email': user.email,
            'name': user.name
        }
    return None

@mpesa_bp.route('/home/', methods=['GET'])
def home():
    return jsonify({'message': 'MPESA API home'})

@mpesa_bp.route('/token', methods=['GET'])
def get_token():
    try:
        token = generate_access_token(consumer_key, consumer_secret)
        return jsonify({'access_token': token})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mpesa_bp.route('/register_urls', methods=['POST'])
def register_urls():
    try:
        access_token = generate_access_token(consumer_key, consumer_secret)
        api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"
        headers = {"Authorization": "Bearer %s" % access_token}
        request_data = {
            "ShortCode": "600987", 
            "ResponseType": "Completed",
            "ConfirmationURL": "https://barnes.onrender.com/m/confirmation",
            "ValidationURL": "https://barnes.onrender.com/m/validation"
        }
        response = requests.post(api_url, json=request_data, headers=headers)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mpesa_bp.route('/validation', methods=['POST'])
def validation():
    data = request.get_json()
    # Process validation logic here
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

@mpesa_bp.route('/confirmation', methods=['POST'])
def confirmation():
    data = request.get_json()
    phone_number = data.get('MSISDN')
    amount = data.get('Amount')

    try:
        amount = Decimal(amount)  # Convert the amount to Decimal
    except (ValueError, InvalidOperation) as e:
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid amount format"}), 400

    # Find the user associated with the phone number
    user = User.query.filter_by(phone_number=phone_number).first()
    if user:
        # Assuming you want to create a payment record
        payment = Payment(
            inventory_id=None,  # Adjust as needed if you associate payments with inventory
            amount=amount
        )
        db.session.add(payment)
        db.session.commit()
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})
    else:
        return jsonify({"ResultCode": 1, "ResultDesc": "User not found"}), 404
