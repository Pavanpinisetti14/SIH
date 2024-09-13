from flask import Flask, request, redirect, jsonify, send_from_directory
from pymongo import MongoClient
import re

app = Flask(__name__, static_folder='public')

# MongoDB connection
mongo_uri = 'mongodb+srv://Arjun:Pavan2003@cluster.pd7vx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster'
client = MongoClient(mongo_uri)
db = client['test']  # Replace 'test' with your actual database name
data_collection = db.data

# Serve static files from 'public' directory
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/')
def home():
    return redirect('/index.html')

@app.route('/signup')
def signup():
    return redirect('/Register.html')

@app.route('/submit', methods=['POST'])
def submit():
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    email = request.form.get('email')
    company = request.form.get('company')
    password = request.form.get('password')
    conpassword = request.form.get('conpassword')

    errors = valid(email, password, conpassword)
    
    if errors:
        return jsonify(errors), 400

    new_data = {
        'firstname': firstname,
        'lastname': lastname,
        'email': email,
        'company': company,
        'password': password
    }

    try:
        data_collection.insert_one(new_data)
        print("Data Successfully Stored")
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login')
def login():
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/loginsubmit', methods=['POST'])
def loginsubmit():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return jsonify({'error': 'Both fields are required'}), 400

    user = data_collection.find_one({'email': email})

    if user:
        if user['password'] == password:
            print("Login Succesfull")
            return redirect('/user.html')  # Use redirect to navigate to user.html
        else:
            return jsonify({'error': 'Invalid password'}), 401
    else:
        return jsonify({'error': 'User not found'}), 404

def valid(email, password, conpassword):
    errors = {}
    
    # Email validation
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        errors['email'] = 'Invalid email address'

    # Password validation
    passregex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    if not passregex.match(password):
        errors['password'] = 'Password must be at least 8 characters long and include a mix of uppercase, lowercase, digits, and special characters'
    
    if password != conpassword:
        errors['conpassword'] = 'Passwords do not match'

    return errors

if __name__ == '__main__':
    app.run(port=1432)
