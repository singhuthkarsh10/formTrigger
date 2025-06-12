from flask import Flask, request, render_template, jsonify
import csv, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='BIA')

# Flask app setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# SMTP config from .env
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 465))

# Load HTML email template
def load_template(name):
    with open('templates/email_template.html', encoding='utf-8') as f:
        template = Template(f.read())
    return template.render(name=name)

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# CSV upload route
@app.route('/send-emails', methods=['POST'])
def send_emails():
    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row.get('Name')
            email = row.get('Email')
            if not name or not email:
                continue
            send_email(name, email)

    return 'All welcome emails sent!'

# Webhook trigger route
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    name = data.get('Name')
    email = data.get('Email')

    if not name or not email:
        return jsonify({'error': 'Missing name or email'}), 400

    try:
        send_email(name, email)
        return jsonify({'message': 'Email sent successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Common function to send email
def send_email(name, email):
    msg = MIMEMultipart()
    msg['Subject'] = "Welcome to the Gen AI Masterclass!"
    msg['From'] = SENDER_EMAIL
    msg['To'] = email

    html_content = load_template(name)
    msg.attach(MIMEText(html_content, 'html'))

    print(f"[INFO] Sending email to {email}...")

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())

    print(f"[✓] Email sent to {email}")

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)