from flask import *
from pymongo import *
import re
import requests
from bs4 import BeautifulSoup
import smtplib
import random
from email.message import EmailMessage
import pandas as pd
import time
import sqlite3

import sys
sys.stdout.flush()
sys.stdout.reconfigure(line_buffering=True)
import os
print(os.getcwd())  # Ensure the script is running in the expected location


app = Flask(__name__, static_folder='public', template_folder='public')
app.secret_key = 'login'
otp = []
email = []


# mongo_uri = os.getenv("MONGO_URI")
client = MongoClient('mongodb+srv://Gayathri:Gayathri23295@cluster0.mkjeg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['test']
data_collection = db.data


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('Register.html')

@app.route('/submit', methods=['POST'])
def submit():
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    email = request.form.get('email')
    company = request.form.get('company')
    password = request.form.get('password')
    conpassword = request.form.get('conpassword')

    
    if valid(email):
        return render_template('Register.html',emailerror=True)
    elif passwordvalid(password):
        return render_template('Register.html',passerror=True)
    elif comparepasswrod(password,conpassword):
        return render_template('Register.html',compasserror=True)
    else:
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
            return render_template('/index.html',success="True")
        except Exception as e:
            print(f"Error: {e}")
            return render_template('/Register.html', alert=True)


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/loginsubmit', methods=['POST'])
def loginsubmit():
    email = request.form.get('email')
    password = request.form.get('password')

    # if not email or not password:
    #     return render_template('/login.html', alert="Invalid Fields")

    user = data_collection.find_one({'email': email})

    if user:
        if user['password'] == password:
            print("Login Successful")
            session['firstname'] = user['firstname']
            session['lastname'] = user['lastname']
            session['email'] = user['email']
            return redirect('/scrape')
        else:
            return render_template('login.html',passalert="Inavlid Password")
    else:
        return render_template('login.html',unamealert="Invalid Email Address")






# Function should be defined before calling


def get_cve_data(cve_number):
    url = f"https://cveawg.mitre.org/api/cve/{cve_number}"
    response = requests.get(url)
    if response.status_code == 200:
        cve_data = response.json()
        cve_id = cve_data["cveMetadata"]["cveId"]
        published_date = cve_data["cveMetadata"]["datePublished"]
        vendor = cve_data["containers"]["cna"]["affected"][0].get("vendor", "N/A")
        product = cve_data["containers"]["cna"]["affected"][0].get("product", "N/A")
        severity = "N/A"
        if "containers" in cve_data and "cna" in cve_data["containers"] and "metrics" in cve_data["containers"]["cna"]:
            metrics = cve_data["containers"]["cna"]["metrics"]
            if metrics and "cvssV4_0" in metrics[0]:
                severity = metrics[0]["cvssV4_0"].get("baseSeverity", "N/A")
        vulnerability_issue = cve_data["containers"]["cna"]["descriptions"][0]["value"]
        return {
            "CVE ID": cve_id,
            "Published Date": published_date,
            "Vendor (Company Name)": vendor,
            "Severity": severity,
            "Product Name": product,
            "Vulnerability Issue": vulnerability_issue
        }
    return None

@app.route('/scrape', methods=['GET'])
def scrape():
    url = "https://nvd.nist.gov/vuln/search/results?form_type=Basic&results_type=overview&search_type=all&isCpeNameSearch=false"
    webdata = requests.get(url)
    data = BeautifulSoup(webdata.content, 'html.parser')
    tabledata = data.find('tbody')
    if not tabledata:
        return jsonify({"error": "Element Not Found!"})
    cve_list = [cve.get_text(strip=True) for rows in tabledata.find_all('tr') for cve in rows.find_all('th')]
    vuln_list = [get_cve_data(cve) for cve in cve_list if get_cve_data(cve)]
    
    df = pd.DataFrame(vuln_list)
    levels = ['MEDIUM', 'HIGH']
    df = df[df['Severity'].isin(levels)]
    table_html = df.to_html(classes='table table-striped', index=False)
    # return  if vuln_list else jsonify({"message": "No vulnerability data found."})
    return render_template('user.html', table_html=table_html, firstname="Gayathri", lastname="Bonu")


@app.route('/logout')
def logout():
    session.pop('email',None) 
    session.pop('firstname',None)
    session.pop('lastname',None)

    response = make_response(render_template('login.html'))
    response.set_cookie('jwt_token', '', expires=0)

    return response

def valid(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return True
    return False

def passwordvalid(password):
    passregex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    if not passregex.match(password):
        return True
    return False

def comparepasswrod(password, conpassword):
    if password != conpassword:
        return True
    return False

@app.route("/forgetpassword")
def forgetpassword():
    return render_template('forgetpassword.html')

@app.route("/sendotp", methods=['POST', 'GET'])
def sendotp():
    generatedotp = random.randint(1000, 9999)
    otp.append(generatedotp)

    sender_email = "alertarcnoreplay@gmail.com"
    sender_password = "cbsm npqr wizh kmhv"

    message = EmailMessage()
    message.set_content(f'Your OTP is: {otp[0]}')
    message['Subject'] = 'Your OTP Code'
    message['From'] = sender_email

    user_email = request.form.get('email')
    email.append(user_email)
    email_record = data_collection.find_one({'email': user_email})
    
    if email_record:
        message['To'] = email_record['email']
    else:
        msg = "Email Address not found. Please enter a valid email."
        return render_template('forgetpassword.html', msg=msg)
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(message)
            print("OTP sent successfully!")
            return render_template('forgetpassword.html', success="OTP sent successfully!")
    except Exception as e:
        errormsg = str(e)
        print(errormsg)
        return render_template('forgetpassword.html', errormsg=errormsg)
@app.route("/verifyOTP", methods=['POST', 'GET']) 
def verifyOTP():
    otp1 = request.form.get('otp1')
    otp2 = request.form.get('otp2')
    otp3 = request.form.get('otp3')
    otp4 = request.form.get('otp4')

    received_otp = int(otp1 + otp2 + otp3 + otp4)

    print("Received OTP:", type(received_otp))
    print("Generated OTP:", type(otp[0])) 

    if otp[0] == received_otp:  
        otp.clear()
        return render_template('forgetpassword.html', otpverify=True)
    else:
        return render_template('forgetpassword.html', otperror=True)

@app.route("/passwordupdate",methods=['POST','GET'])
def passwordupdate():
    password = request.form.get('password')
    conformpassword = request.form.get('conformpassword')

    if password == conformpassword :
        user_email = email[0]
        print("Email ",user_email)
        if user_email:
            data_collection.update_one(
                {'email': user_email}, 
                {'$set': {'password': password}}
            )
            email.clear()
            print("Password updated successfully!")
            return render_template('login.html', success="Password updated successfully!")
        else:
            print("mail Not found Doesn't Match")
            return render_template('forgetpassword.html', otpverify=True)
    else:
         print("Password Doesn't Match")
         return render_template('forgetpassword.html', otpverify=True)
    
if __name__ == "__main__":
    app.run(port=1432,debug=True)  # Start Flask server
