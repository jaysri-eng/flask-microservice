#import or add modules 
import requests 
from flask import Flask, jsonify, request, make_response
import jwt
from functools import wraps
import json
import os
from jwt.exceptions import DecodeError
import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE = os.getenv("DB_DATABASE")

# Create the configuration dictionary
config = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_DATABASE
}

mydb = mysql.connector.connect(**config)
cursor = mydb.cursor()

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
port = int(os.environ.get('PORT',5000))
@app.route("/")

#define the home function
def home():
    return "Welcome"
if __name__=="__main__":
    app.run(debug=True,host="0.0.0.0",port=port)

#function for getting the products details from the api
BASE_URL = "https://dummyjson.com"
with open('users.json', 'r') as f:
    users = json.load(f)
@app.route('/auth', methods=['POST'])
def authenticate_user():
    if request.headers['Content-Type'] != 'application/json':
        return jsonify({'error': 'Unsupported Media Type'}), 415
    username = request.json.get('username')
    password = request.json.get('password')
    for user in users:
        if user['username'] == username and user['password'] == password:
            token = jwt.encode({'user_id': user['id']}, app.config['SECRET_KEY'],algorithm="HS256")
            response = make_response(jsonify({'message': 'Authentication successful'}))
            response.set_cookie('token', token)
            return response, 200
    return jsonify({'error': 'Invalid username or password'}), 401

#function to get particular product details to put into cart table 
@app.route('/getSomeDetails', methods=['GET'])
def get_products():
    cursor.execute("SELECT id, title, price FROM products")
    response = cursor.fetchall()
    products = []
    for product in response:
        product_data = {
            'id': product[0],
            'title': product[1],
            'price': product[2]
        }
        products.append(product_data)

    return jsonify({'data': products}), 200 if products else 204
    # products = cursor.fetchall()
    # return jsonify([{'id': product[0], 'title': product[1], 'price': product[2]} for product in products])

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

@app.route('/addProducts',methods=['POST'])
def addProduct():
    # Extract token from request headers
    token = request.cookies.get('token')

    # Validate token (e.g., check if it's present and valid)
    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    data = request.get_json()
    id = data.get('id')
    title = data.get('title')
    brand = data.get('brand')
    price = data.get('price')
    descrip = data.get('descrip')

    if not all([title, brand, price]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Insert data into MySQL database
    query = "INSERT INTO products (id, title, brand, price, descrip) VALUES (%s, %s, %s, %s, %s)"
    values = (id, title, brand, price, descrip)
    
    try:
        cursor.execute(query, values)
        mydb.commit()
        return jsonify({'message': 'Product added successfully'}), 201
    except Exception as e:
        mydb.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        mydb.close()

@app.route('/deleteProduct',methods=['POST'])
def deleteProduct():
    # Extract token from request headers
    token = request.cookies.get('token')

    # Validate token (e.g., check if it's present and valid)
    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    data = request.get_json()
    id = data.get('id')
    if not id:
        return jsonify({'error': 'Missing product id'}), 400
    query = "DELETE FROM products WHERE id = %s"
    values = (id,)
    try:
        cursor.execute(query, values)
        mydb.commit()
        return jsonify({'message': 'Product deleted successfully'}), 201
    except Exception as e:
        mydb.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        mydb.close()
