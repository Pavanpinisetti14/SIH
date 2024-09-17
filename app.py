from flask import Flask, request, redirect, jsonify, send_from_directory, render_template, session
from pymongo import MongoClient
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__, static_folder='public', template_folder='public')
app.secret_key = 'login'

# MongoDB Connection
mongo_uri = 'mongodb+srv://Arjun:Pavan2003@cluster.pd7vx.mongodb.net/test?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true'
client = MongoClient(mongo_uri)
db = client['test']
data_collection = db.data

# Static file serving
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/signup')
def signup():
    return send_from_directory(app.static_folder, 'Register.html')

# User registration
@app.route('/submit', methods=['POST'])
def submit():
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    email = request.form.get('email')
    company = request.form.get('company')
    password = request.form.get('password')
    conpassword = request.form.get('conpassword')

    # Validate form data
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
        return render_template('/index.html', alert=True)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('/Register.html', alert=False)

# User login
@app.route('/login')
def login():
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/loginsubmit', methods=['POST'])
def loginsubmit():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return render_template('/user.html', alert=True)

    user = data_collection.find_one({'email': email})

    if user:
        if user['password'] == password:
            print("Login Successful")
            # Store user details in session
            # print(user['firstname'])
            session['firstname'] = user['firstname']
            session['lastname'] = user['lastname']
            session['email'] = user['email']
            return redirect('/scrape')
        else:
            return render_template('/login.html', passalert=True)
    else:
        return render_template('/login.html', useralert=True)

# Scrape data from the website and filter it by last name
@app.route('/scrape')
def scrape():
    url = "https://oem-xi.vercel.app/"
    webdata = requests.get(url)
    data = BeautifulSoup(webdata.content, 'html.parser')

    tabeldata = data.find('table', id='vulnTable')
    if not tabeldata:
        return "Element Not Found!"

    li = []
    row = tabeldata.find_all('tr')
    for rows in row:
        col = rows.find_all('td')
        tabel = [cols.get_text(strip=True) for cols in col]
        li.append(tabel)

    if li:
        li.pop(0)  

    # Define column names
    columns = ["Company Name", "Product", "Manufacturing Date", "Issuses/Vulnerability's", "Level","Company Email", "Category","Code Name"]
    df = pd.DataFrame(li, columns=columns)
    df = df[df['Company Email'] == session.get('email')]

    levels = ['Critical', 'High']
    df = df[df['Level'].isin(levels)]

    print("Filtered DataFrame based on user's email and Level:")
    print(df) 

    # Convert DataFrame to HTML for rendering
    table_html = df.to_html(classes='table table-striped', index=False)
    print(session)
    # Get user details from session
    firstname = session.get('firstname','')
    lastname = session.get('lastname', '')

    return render_template('user.html', table_html=table_html, firstname=firstname, lastname=lastname)

# Form data validation function
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

# Run the app
if __name__ == '__main__':
    app.run(port=1432, debug=True)
