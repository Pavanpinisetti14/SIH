from flask import *
from pymongo import *
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import smtplib
import random
from email.message import EmailMessage

app = Flask(__name__, static_folder='public', template_folder='public')
app.secret_key = 'login'
otp = []
email = []
mongo_uri = 'mongodb+srv://Arjun:Pavan2003@cluster.pd7vx.mongodb.net/test?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true'
client = MongoClient(mongo_uri)
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

   
    columns = ["Company Name", "Product", "Manufacturing Date", "Issuses/Vulnerability's", "Level","Company Email", "Category","Code Name"]
    df = pd.DataFrame(li, columns=columns)
    df = df[df['Company Email'] == session.get('email')]

    levels = ['Critical', 'High']
    df = df[df['Level'].isin(levels)]

    table_html = df.to_html(classes='table table-striped', index=False)
    # print(session)
   
    firstname = session.get('firstname','')
    lastname = session.get('lastname', '')

    return render_template('user.html', table_html=table_html, firstname=firstname, lastname=lastname)

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
    
if __name__ == '__main__':
    app.run(port=1432, debug=True)
