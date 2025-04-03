#!/usr/bin/python
"""
Test email functionality for the Wallabot application.

This script allows testing the email delivery system using dummy data
to verify that emails are correctly formatted and delivered.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config as cfg
import email_template

def test_email():
    """
    Test the email sending functionality with current styling.
    
    Creates sample data and sends a test email using the configured
    email settings in config.py. This helps verify that the email
    templates are working correctly and that credentials are valid.
    """
    print("Starting email test...")
    print(f"Email configuration:")
    print(f"- Username: {cfg.username}")
    print(f"- Receiver: {cfg.receiver}")
    
    # Create test offers with complete dummy data
    test_offers = [
        {
            'titulo': 'PlayStation 5 Digital Edition (Como nueva)',
            'precio': '500€',
            'enlace': 'https://es.wallapop.com/item/playstation-5-digital-edition-123456',
            'reservada': False,
            'seller_name': 'María García',
            'seller_number_of_rates': '42',
            'seller_rate': '4.8',
            'seller_sales': '18',
            'location': 'Madrid',
            'shipping': 'Sí',
            'image_url': 'https://cdn.wallapop.com/images/10420/dj/wi/__/c10420p826133360/i2897532934.jpg'
        },
        {
            'titulo': 'PlayStation 5 Pro 30th Anniversary Edition',
            'precio': '599€',
            'enlace': 'https://es.wallapop.com/item/playstation-5-pro-30th-anniversary-567890',
            'reservada': True,
            'seller_name': 'Carlos Rodríguez',
            'seller_number_of_rates': '123',
            'seller_rate': '4.9',
            'seller_sales': '57',
            'location': 'Barcelona',
            'shipping': 'No',
            'image_url': 'https://cdn.wallapop.com/images/10420/gk/rz/__/c10420p912345678/i3456789012.jpg'
        },
        {
            'titulo': 'PlayStation 5 + 2 Mandos + 3 Juegos',
            'precio': '550€',
            'enlace': 'https://es.wallapop.com/item/playstation-5-con-accesorios-112233',
            'reservada': False,
            'seller_name': 'Javier López',
            'seller_number_of_rates': '8',
            'seller_rate': '3.5',
            'seller_sales': '3',
            'location': 'Valencia',
            'shipping': 'Sí',
            'image_url': 'https://cdn.wallapop.com/images/10420/ab/cd/__/c10420p987654321/i3141592654.jpg'
        }
    ]
    
    # Setup mail server
    try:
        # Select the appropriate mail server based on the email domain
        if '@gmail.com' in cfg.username:
            server = smtplib.SMTP("smtp.gmail.com", port=587)
            server.starttls()
            print("Using Gmail SMTP server")
        else:
            server = smtplib.SMTP("smtp.sapo.pt", port=587)
            server.starttls()
            print("Using Sapo SMTP server")
        
        server.set_debuglevel(1)  # Enable debug output
        
        try:
            print(f"Attempting login with username: {cfg.username}")
            server.login(cfg.username, cfg.password)
            print("Login successful!")
        except smtplib.SMTPAuthenticationError as e:
            print(f"SMTP Authentication Error: {e}")
            print("\nFor Gmail accounts, you need to:")
            print("1. Enable 2-factor authentication: https://myaccount.google.com/security")
            print("2. Create an app password: https://myaccount.google.com/apppasswords")
            print("3. Use that app password in config.py instead of your regular password")
            server.quit()
            return

        # Setup message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Wallabot Test Email"
        message["From"] = cfg.username
        message["To"] = cfg.receiver

        # Generate email content using the template module
        text = email_template.generate_text_body(test_offers)
        html = email_template.generate_html_body(
            test_offers,
            title="Wallabot Email Test",
            intro="Dummy data for testing. Don't panic.",
            footer="This is a test email sent from Wallabot to verify a correct functionality."
        )

        # Attach parts
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)

        # Send email
        print("Sending test email...")
        server.sendmail(cfg.username, cfg.receiver, message.as_string())
        print("Email sent successfully!")
        
    except Exception as e:
        print(f"Error sending test email: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            server.quit()
            print("SMTP connection closed")
        except:
            pass

if __name__ == "__main__":
    test_email() 