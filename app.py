from flask import Flask, request, render_template, jsonify
import csv, os, qrcode, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from jinja2 import Template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='BIA')

# Flask app setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('qrcodes', exist_ok=True)

# SMTP config from .env
SENDER_EMAIL = 'biamanyata@gmail.com'
SENDER_PASSWORD = 'tsir ixwj pfme mkjp'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465

# Load HTML email template
def load_template(name):
    with open('templates/email_template.html', encoding='utf-8') as f:
        template = Template(f.read())
    return template.render(name=name)

# Generate QR code
def generate_qr_code(name, email):
    safe_name = name.replace(" ", "_").replace("@", "_at_")
    filename = f"{safe_name}_{email}.png"
    path = os.path.join("qrcodes", filename)
    data = f"Name: {name}\nEmail: {email}"
    img = qrcode.make(data)
    img.save(path)
    return path

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
            send_email_with_qr(name, email)
    return 'All emails sent with QR codes!'

# Webhook trigger route
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    name = data.get('Name')
    email = data.get('Email')

    if not name or not email:
        return jsonify({'error': 'Missing name or email'}), 400

    try:
        send_email_with_qr(name, email)
        return jsonify({'message': 'Email sent successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Common function to send email with QR
def send_email_with_qr(name, email):
    qr_path = generate_qr_code(name, email)
    msg = MIMEMultipart()
    msg['Subject'] = "Your Gen AI Masterclass Registration Confirmation"
    msg['From'] = SENDER_EMAIL
    msg['To'] = email

    html_content = load_template(name)
    msg.attach(MIMEText(html_content, 'html'))

    with open(qr_path, 'rb') as img:
        image = MIMEImage(img.read())
        image.add_header('Content-ID', '<qr_code>')
        image.add_header('Content-Disposition', 'attachment', filename='qr_code.png')
        msg.attach(image)

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
    print(f"[✓] Sent to {email}")

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)