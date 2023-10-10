import argparse
import base64
import csv
import http.client
import json
import os
import os.path as path
import secrets
import shutil
import string
import sys
import time
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import bcrypt  # bcrypt
import boto3
import mysql.connector  # mysql-connector-python
import requests
import urllib3
from urllib3.contrib import pyopenssl

alphabet = string.ascii_letters + string.digits
auth0_endpoint = ""

def load_logo_attachment(filename):
    with open(filename, "rb") as f:
        attachment = MIMEImage(f.read())
        attachment.add_header("Content-Disposition", "inline", filename=filename)
        attachment.add_header("Content-ID", "<logo_image>")
        return attachment

# recipients and cc_recipients should be lists of emails
# attachments should be a list of MIMEBase objects, one for each attachment
def send_html_email(subject, body, recipients, ses, cc_recipients=None, attachments=None, alternative_text=None):
    message = MIMEMultipart("mixed")
    message.set_charset("utf8")

    if type(recipients) == str:
        recipients = [recipients]

    all_recipients = [r.strip() for r in recipients]
    message["to"] = ", ".join(recipients)
    message["from"] = ""

    if cc_recipients:
        if type(cc_recipients) == str:
            cc_recipients = [cc_recipients]
        message["cc"] = ", ".join(cc_recipients)
        all_recipients += [r.strip() for r in cc_recipients]

    message["subject"] = subject
    message_text = MIMEMultipart("alternative")
    if alternative_text:
        message_text.attach(MIMEText(alternative_text, "plain", "utf8"))
    message_text.attach(MIMEText(body, "html", "utf8"))
    message.attach(message_text)

    if attachments:
        for a in attachments:
            encoders.encode_base64(a)
            message.attach(a)

    if ses:
        response = ses.send_raw_email(
            Source="",
            Destinations=all_recipients,
            RawMessage={
                "Data": message.as_bytes()
            })
        print(response)

def load_already_registered():
    res = {}
    if path.exists("registered.json"):
        with open("registered.json", "r") as f:
            res = json.load(f)
    return res


def format_to_auth0(email, name, password, password_hash):
    return {
        "email": email,
        "email_verified": True,
        "name": name,
        "password_hash": password_hash.decode('utf-8'),
    }


def get_access_token():
    conn = http.client.HTTPSConnection("")

    client_id = ""
    client_secret = ""
    payload = f"{\"client_id\":\"{client_id}\",\"client_secret\":\"{client_secret}\",\"audience\":\"{auth0_endpoint}\",\"grant_type\":\"client_credentials\"}"

    headers = {'content-type': "application/json"}

    conn.request("POST", "/oauth/token", payload, headers)

    res = conn.getresponse()
    data = res.read()

    ob = json.loads(data.decode("utf-8"))
    return ob["access_token"]

def send_to_auth0(filename, access_token, connection_id):
    payload = {
        "connection_id": connection_id,
        "external_id": "import_user",
        "send_completion_email": False
    }

    files = {
        "users": open(filename, "rb")
    }

    headers = {
        'authorization': f"Bearer {access_token}"
    }

    response = requests.post(f"{auth0_endpoint}/jobs/users-imports", data=payload, files=files,
                             headers=headers)

    print(response.content)

def authenticate_ses():
    with open("aws.json", "r") as f:
        auth = json.load(f)
        ses = boto3.client("ses",
                aws_access_key_id=auth["access_key"],
                aws_secret_access_key=auth["secret_key"],
                region_name="us-east-2")
        return ses

def send_register_email(email, ses, logo_attachment, name, password):
    # Send them an email with the account name and password
    email_html = f"""
            <p>Dear {name},</p>
            <p>Thank you for registering for VIS2020! We have a great week scheduled of paper
            presentations, workshops, tutorials, panels, and more!
            This email contains your login information for the virtual conference website:
            <a href="https://virtual.ieeevis.org/">https://virtual.ieeevis.org/</a>.
            The website contains the conference schedule, links to
            the YouTube videos and Discord chat channels for each session, and links to download
            the papers. Try shuffling the <a href="https://virtual.ieeevis.org/papers.html">paper browser</a> by serendipity to find
            something totally new!
            </p>
            <ul>
            <li><b>User name:</b> {email}</li>
            <li><b>Password:</b> {password}</li>
            <li><b>Discord Invite:</b> </li>
            </ul>
            <img width='400' src='cid:logo_image' alt='Logo'/>
            """
    plain_text = f"""
            Dear {name},

            Thank you for registering for VIS2020! We have a great week scheduled of paper
            presentations, workshops, tutorials, panels, and more!
            This email contains your login information for the virtual conference website:
            https://virtual.ieeevis.org/.
            The website contains the conference schedule, links to
            the YouTube videos and Discord chat channels for each session, and links to download
            the papers. Try shuffling the paper browser https://virtual.ieeevis.org/papers.html by serendipity to find
            something totally new!

            User name: {email}

            Password: {password}

            Discord Invite:
            """

    send_html_email("VIS 2020 Registration", email_html, email, ses,
            alternative_text=plain_text,
            attachments=[logo_attachment])


def get_all_from_db():
    mydb = mysql.connector.connect(
        host="",
        user="",
        password="",
        database=""
    )

    name_attrib = ""
    email_attrib = ""
    mycursor = mydb.cursor()
    mycursor.execute(f"SELECT {name_attrib}, {email_attrib} FROM appointments")
    return mycursor.fetchall()

def get_all_from_cvent(file_name):
    all_cvent = []
    with open(file_name, 'r', encoding="utf8") as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        for line in csv_reader:
            if "," in line:
                last, first = line[0].split(', ')
                all_cvent.append([f"{first} {last}", line[1]])
            elif len(line) > 0:
                all_cvent.append([line[0], line[1]])
            else:
                break
    return all_cvent

# Check for any new_cvent_* files with new cvent registrations
def check_any_cvent():
    all_cvent = []
    for f in os.listdir("./"):
        if f.startswith("new_cvent_"):
            all_cvent += get_all_from_cvent(f)
            shutil.move(f, "processed_" + f)
    print(f"From new cvent got: {all_cvent}")
    return all_cvent

def get_any_password_requests():
    password_requests = []
    for f in os.listdir("./"):
        if f.startswith("password_request"):
            with open(f, "r") as fhandle:
                for l in fhandle.readlines():
                    line = l.strip()
                    if len(line) > 0:
                        password_requests.append(line)
    print(f"Got password requests {password_requests}")
    return password_requests

def get_all(transmit_to_auth0, ses, logo_attachment, max_new=-1):
    print('connecting to Tina...')
    results = check_any_cvent() + get_all_from_db()
    password_requests = get_any_password_requests()
    all_registered = load_already_registered()

    all_new = []
    for email, x in all_registered.items():
        if "emailed" not in x:
            x["emailed"] = False
        if not x["emailed"]:
            results.append([x["name"], x["email"]])

    now = str(datetime.utcnow())
    for x in results:
        name, email = x
        if max_new > 0 and len(all_new) >= max_new:
            break
        if len(email) == 0:
            continue
        # We use this same process to re-send someone their login info, so they could be
        # already registered
        if email not in all_registered or not all_registered[email]["emailed"]:
            print(f"adding {email}")
            # "random" password
            password = ""
            if email not in all_registered:
                password = ''.join(secrets.choice(alphabet) for i in range(10)).encode("utf-8")
            else:
                password = all_registered[email]["password"]

            salt = bcrypt.gensalt(rounds=10)
            password_hash = bcrypt.hashpw(password, salt)

            all_new.append(format_to_auth0(email, name, password, password_hash))
            all_registered[email] = {"name": name,
                                     "email": email,
                                     "password": password.decode('utf-8'),
                                     "date": now,
                                     "emailed": False}
        elif email in password_requests:
            print(f"Password request for {email}")
        else:
            continue
        password = all_registered[email]["password"]

        if ses:
            time.sleep(1)

        try:
            send_register_email(email, ses, logo_attachment, name, password)
            if ses:
                all_registered[email]["emailed"] = True
        except Exception as e:
            print("Error sending email {}".format(e))

    print(f"Got {len(all_new)} new registrations")

    registration_stats = {}
    registration_stats_file = "registration_stats.json"
    if os.path.isfile(registration_stats_file):
        with open("registration_stats.json", "r") as f:
            registration_stats = json.load(f)
        registration_stats["new_since_last"] += len(all_new)
    else:
        registration_stats["new_since_last"] = len(all_new)

    print(registration_stats)
    if registration_stats["new_since_last"] >= 100:
        print(f"Got {registration_stats['new_since_last']} new registrations since last notice! Sending email")
        email_html = f"""
        <p>There have been <b>{registration_stats["new_since_last"]}</b> new registrations!
        There are now {len(all_registered)} attendees registered for VIS.</p>
        """
        plain_text = f"""
        There have been {registration_stats["new_since_last"]} new registrations!
        There are now {len(all_registered)} attendees registered for VIS.
        """
        send_html_email("VIS 2020 Registration Count Update", email_html,
                [], ses, alternative_text=plain_text)
        registration_stats["new_since_last"] = 0

    with open(registration_stats_file, "w") as f:
        json.dump(registration_stats, f)

    if len(all_new) > 0:
        file_name = f"new_imports_{time.time_ns() / 1000}.json"
        with open(file_name, "w") as f:
            json.dump(all_new, f)
        if transmit_to_auth0:
            print("Sending to Auth0")
            token = get_access_token()
            send_to_auth0(file_name, token, "con_syD4BrJWi0r09tSl")
            with open("registered.json", "w") as f:
                json.dump(all_registered, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--mail', action="store_true", help='send email for new users')
    parser.add_argument('--auth0', action="store_true", help='send new users to auh0')
    parser.add_argument('--limit', default=-1, type=int, help='maximum number of new users for this run')

    args = parser.parse_args()

    print(args, args.auth0)
    ses = None
    if args.mail:
        ses = authenticate_ses()

    logo_attachment = load_logo_attachment("./vis2020 logo.png")

    while True:
        print("Checking for new registrations")
        get_all(args.auth0, ses, logo_attachment, args.limit)
        time.sleep(5 * 60)

