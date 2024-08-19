from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# Configure email settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use your email server
app.config['MAIL_PORT'] = 587  # Use the appropriate port for your server
app.config['MAIL_USERNAME'] = 'emungai906@gmail.com'  # Your email address
app.config['MAIL_PASSWORD'] = 'wplz rpce ffvj bjoe'  # Your email password (or app-specific password)
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

@app.route("/")
def index():
    msg = Message(
        subject="Hello",
        sender="eddnjoori@gmail.com",
        recipients=["njooriedmound@gmail.com"],
        body="This is a test email from Flask!"
    )
    try:
        mail.send(msg)
        return "Email sent successfully!"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)
