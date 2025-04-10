import base64
import datetime
import requests
from django.conf import settings

def get_mpesa_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    response = requests.get(url, auth=(consumer_key, consumer_secret))
    data = response.json()
    return data.get('access_token')

def initiate_stk_push(phone_number, amount, order_id):
    access_token = get_mpesa_access_token()
    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        (settings.MPESA_BUSINESS_SHORTCODE + settings.MPESA_PASSKEY + timestamp).encode()
    ).decode()
    
    payload = {
        "BusinessShortCode": settings.MPESA_BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": settings.MPESA_BUSINESS_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"ORDER{order_id}",
        # "TransactionDesc": "Food Order Payment"
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()