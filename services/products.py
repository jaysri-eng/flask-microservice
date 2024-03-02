#import or add modules 
import requests 
from flask import Flask, jsonify, request, make_response
import jwt
from functools import wraps
import json
import os
from jwt.exceptions import DecodeError

#initiate flask app and assign JWT toke for authentication
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

#function for authenticating the JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return jsonify({'error': 'Authorization token is missing'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except DecodeError:
            return jsonify({'error': 'Authorization token is invalid'}), 401
        return f(current_user_id, *args, **kwargs)
    return decorated

#mention the port number and assign app routes 
port = int(os.environ.get('PORT',5001))
@app.route("/")

#define the home function
def home():
    return "Welcome"
if __name__=="__main__":
    app.run(debug=True,host="0.0.0.0",port=port)

#function for getting the products details from the api
BASE_URL = "https://dummyjson.com"
@app.route('/products', methods=['GET'])
@token_required
def getProducts(user_id):
    headers = {'Authorization': f'Bearer {request.cookies.get("token")}'}
    response = requests.get(f"{BASE_URL}/products", headers=headers)
    if response.status_code!=200:
        return jsonify({'error':response.json()['message']}), response.status_code
    products=[]
    for product in response.json()['products']:
        product_data = {
            'id': product['id'],
            'title': product['title'],
            'brand': product['brand'],
            'price': product['price'],
            'description': product['description']
        }
        products.append(product_data)
    return jsonify({'data':products}),200 if products else 204
