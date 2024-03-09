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
from werkzeug.security import check_password_hash

# Load environment variables from .env file
load_dotenv()

# Access environment variables
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_USER_DATABASE = os.getenv("DB_USER_DATABASE")

# Create the configuration dictionary
config = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_USER_DATABASE
}

mydb = mysql.connector.connect(**config)
cursor = mydb.cursor()
cursor.execute("USE user")
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

with open('users.json', 'r') as f:
    users = json.load(f)

@app.route('/signup',methods=['POST'])
def signup():
    data = request.get_json()
    id = data.get('id')
    username = data.get('username')
    password = data.get('password')
    if not all([id, username, password]):
        return jsonify({'error': 'Missing required fields'}), 400
    # Insert data into MySQL database
    query = "INSERT INTO users (id, username, password) VALUES (%s, %s, %s)"
    values = (id, username, password)
    try:
        cursor.execute(query, values)
        mydb.commit()
        return jsonify({'message': 'User added successfully'}), 201
    except Exception as e:
        mydb.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        mydb.close()

@app.route('/login',methods=['POST'])
def login():
    data = request.get_json()
    id = data.get('id')
    username = data.get('username')
    password = data.get('password')
    if not all([id, username, password]):
        return jsonify({'error': 'Missing required fields'}), 400
    if request.headers['Content-Type'] != 'application/json':
        return jsonify({'error': 'Unsupported Media Type'}), 415
    query = "SELECT id, username, password FROM users WHERE id = %s AND username = %s AND password = %s"
    values = (id, username, password,)
    cursor.execute(query,values)
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if user[1] == username and user[2] == password:
        token = jwt.encode({'user_id': user[0]}, app.config['SECRET_KEY'],algorithm="HS256")
        response = make_response(jsonify({'message': 'Login successful'}))
        response.set_cookie('token', token)
        return response, 200, {'token':token}
    cursor.close()
    mydb.close()

@app.route('/logout',methods=['GET'])
def logout():
    # Clear the authentication token cookie
    response = make_response(jsonify({'message': 'Logout successful'}))
    response.set_cookie('token', '', expires=0)
    return response, 200