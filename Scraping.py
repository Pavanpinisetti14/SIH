import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
from pymongo import MongoClient
import smtplib
from email.message import EmailMessage

def get_cve_data(cve_number):
    url = f"https://cveawg.mitre.org/api/cve/{cve_number}"
    response = requests.get(url)

    if response.status_code == 200:
        cve_data = response.json()

        cve_id = cve_data["cveMetadata"]["cveId"]
        published_date = cve_data["cveMetadata"]["datePublished"].split("T")[0]
        vendor = cve_data["containers"]["cna"]["affected"][0].get("vendor", np.nan)
        product = cve_data["containers"]["cna"]["affected"][0].get("product", np.nan)
        severity = np.nan
        
        metrics = cve_data["containers"]["cna"].get("metrics", [])
        if metrics:
            for metric in metrics:
                for key in ["cvssV4_0", "cvssV3_1", "cvssV3_0", "cvssV2_0"]:
                    if key in metric:
                        severity = metric[key].get("baseSeverity", np.nan)
                        break
        
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

def send_email(data):
    sender_email = "alertarcnoreplay@gmail.com"
    sender_password = "cbsm npqr wizh kmhv"

    # df = pd.DataFrame([data])
    # print(df)
    print(data)
    cvenumber = data['CVE ID']
    published = data['Published Date']
    # chaneg the company name what you write in your database
    cmpn = data['Vendor (Company Name)']
    sv = data['Severity']
    pn = data['Product Name']
    vi = data['Vulnerability Issue']
    
    message = EmailMessage()
    message.set_content(f'We Found A New Vulnerability In Your Product\n CVE Number : {cvenumber}\n Published Date : {published} \n Company name : {cmpn} \n Serverity : {sv} \n Product Name: {pn} \n Vulnerabilities Issue : {vi}')
    message['Subject'] = 'New Vulnerability Alert'
    message['From'] = sender_email
    
    # mi database lo company yala unndho alaga evali 
    # email_record = collection.find_one({{"company": data['Company Name']}})
    
    email_record = {"email": "bonugayathri3@gmail.com"}

    if email_record:
        message['To'] = email_record['email']
    else:
        print("Email Address not found.")
        return

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(message)
            print("Mail Sent...")
    except Exception as e:
        print("Error sending email:", e)

def store_database(record):
    # print("Records : ",record)
    try:
        if not data_collection.find_one({"CVE ID": record["CVE ID"]}):
            data_collection.insert_one(record)
            send_email(record)
            return "New vulnerability inserted successfully into MongoDB!"
        else:
            return "Vulnerability already exists in the database."
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Scraping CVE IDs from NVD website
li = []
url = "https://nvd.nist.gov/vuln/search/results"
headers = {"User-Agent": "Mozilla/5.0"}

client = MongoClient('mongodb+srv://Arjun:Pavan2003@cluster.pd7vx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster')
db1 = client['test']
collection = db1.data

db = client['Records']
data_collection = db.data
    
max_retries = 5
for attempt in range(max_retries):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        break
    time.sleep(10)

if response.status_code == 200:
    data = BeautifulSoup(response.content, "html.parser")
    tabledata = data.find("tbody")
    if not tabledata:
        print("No table data found, exiting...")
        exit()

    for rows in tabledata.find_all("tr"):
        for cve in rows.find_all("th"):
            li.append(cve.get_text(strip=True))

    print("CVE Numbers Successfully Scraped")

    # Fetch CVE details and filter out None results
    vuln_list = [get_cve_data(cvenum) for cvenum in li]
    vuln_list = [v for v in vuln_list if v]  # Remove None values

    df = pd.DataFrame(vuln_list).dropna()

    print("CVE Data successfully Scraped")

    if not df.empty:
        for index, row in df.iterrows():
            print(store_database(row.to_dict()))
    else:
        print("No new data to store.")
else:
    print("Failed to fetch data after multiple attempts.")
