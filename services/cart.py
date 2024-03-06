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
from products import config

# Load environment variables from .env file
load_dotenv()

# Access environment variables
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_CART_DATABASE = os.getenv("DB_CART_DATABASE")

# Create the configuration dictionary
config = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_CART_DATABASE
}

mydb = mysql.connector.connect(**config)
cursor = mydb.cursor()
cursor.execute("USE cart")
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
if __name__ == '__main__':
    app.run(debug=True)
# app.run(debug=True,host="0.0.0.0",port=port)

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

#api route and function to add item by fetching product items with id
@app.route('/addProductToCart',methods=['POST'])
def addToCart():
    data = request.get_json()
    id = data.get("id")
    cursor.execute("USE products")
    # Fetch product details from products database
    cursor.execute("SELECT id, title, price FROM products WHERE id = %s", (id,))
    product = cursor.fetchone()

    if not product:
        return jsonify({'error': 'Product not found'}), 404
    cursor.execute("USE cart")
    # Insert product details into cart database
    cursor.execute("INSERT INTO cart (id, item, price) VALUES (%s, %s, %s)",
                   (product[0], product[1], product[2]))
    mydb.commit()
    return jsonify({'message': 'Product added to cart successfully'}), 201

#test function and route to add items directly into cart 
@app.route('/addItems',methods=['POST'])
def addItems():
    data = request.get_json()
    id = data.get('id')
    item = data.get('item')
    price = data.get('price')

    if not all([id, item, price]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Insert data into MySQL database
    query = "INSERT INTO cart (id, item, price) VALUES (%s, %s, %s)"
    values = (id, item, price)
    
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

@app.route('/deleteFromCart',methods=['POST'])
def deleteProduct():
    data = request.get_json()
    id = data.get('id')
    if not id:
        return jsonify({'error': 'Missing product id'}), 400
    query = "DELETE FROM cart WHERE id = %s"
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