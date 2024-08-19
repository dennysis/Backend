from flask import Blueprint, request, jsonify
import requests
import json


mpesa_bp = Blueprint('mpesa', __name__)

@mpesa_bp.route('/mpesa_payment', methods=['POST'])
def mpesa_payment():
    data = request.get_json()
    phone_number = data.get('phone_number')
    amount = data.get('amount')
    user_id = data.get('user_id')

    # M-Pesa API details
    lipa_na_mpesa_online_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",  # Replace with actual token
        "Content-Type": "application/json",
    }
    payload = {
        "BusinessShortCode": "YOUR_SHORTCODE",
        "Password": "YOUR_PASSWORD",
        "Timestamp": "YOUR_TIMESTAMP",
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": "YOUR_SHORTCODE",
        "PhoneNumber": phone_number,
        "CallBackURL": "https://example.com/callback",
        "AccountReference": "Test123",
        "TransactionDesc": "Payment for testing"
    }

    response = requests.post(lipa_na_mpesa_online_url, headers=headers, json=payload)

    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": "Failed to initiate payment"}), response.status_code
