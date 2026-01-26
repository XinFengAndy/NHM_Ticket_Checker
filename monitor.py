import requests
import smtplib
import json
import os
import sys
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def send_email(subject, body):
    # Load secrets
    receiver_email = os.environ.get('RECEIVER')
    sender_email = os.environ.get('SENDER_USER')
    sender_password = os.environ.get('SENDER_PASS')

    # Validate ALL credentials
    if not sender_email or not sender_password or not receiver_email:
        print("Error: Email credentials (SENDER_USER, SENDER_PASS, or RECEIVER) not found in env vars.")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Using Gmail's SMTP server by default.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print(f"Email sent to {receiver_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_tickets():
    config = load_config()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(config['url'], headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

    # Parse date range
    start_date = datetime.strptime(config['start_date'], "%Y-%m-%d")
    end_date = datetime.strptime(config['end_date'], "%Y-%m-%d")

    available_dates = []

    for item in data:
        # API returns dateTime like "2026-02-16T00:00:00"
        item_date_str = item.get('dateTime', '').split('T')[0]
        try:
            item_date = datetime.strptime(item_date_str, "%Y-%m-%d")
        except ValueError:
            continue

        # Check if date is within range
        if start_date <= item_date <= end_date:
            has_offers = item.get('hasOffers', False)
            sold_out = item.get('soldOut', True)

            # Condition: hasOffers is True OR soldOut is False
            if has_offers or not sold_out:
                available_dates.append(f"{item_date_str} (Availability: {item.get('availability', 'Unknown')})")

    if available_dates:
        print("Tickets found! Sending email...")
        subject = "TICKET ALERT: NHMPE Tickets Available!"
        body = f"Tickets are available for the following dates:\n\n" + "\n".join(available_dates) + f"\n\nLink: {config['url']}"
        send_email(subject, body)
    else:
        print("No tickets found matching criteria.")

if __name__ == "__main__":
    check_tickets()
