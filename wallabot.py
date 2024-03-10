#!/usr/bin/python
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from selenium.common.exceptions import NoSuchElementException
import pickle
import os
import config as cfg
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def sendMail(offers):
    '''Build message with current offers and send them'''
    # Setup mail server
    server = smtplib.SMTP("smtp.sapo.pt", port=587)
    server.starttls()
    server.set_debuglevel(False)

    try:
        server.login(cfg.username, cfg.password)
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        server.quit()

    # Setup message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Retroid Pocket"
    message["From"] = cfg.username
    message["To"] = cfg.receiver

    # write the text/plain part
    offers_text_array = ['{} precio: {} link: {}, {}'.format(n['titulo'], n['precio'],n['enlace'], "reservada" if n['reservada'] else "disponível") for n in offers]
    
    text = "".join([str(item) for item in offers_text_array])
    
    # write the HTML part
    offers_html_array = [
        '<p>{} | {}</p>\n'
        '<a href="{}">LINK</a> | {} \n'
        '<p></p>\n'
        '<br>\n'
        '<br>\n'
        '___________________________\n'
        '___________________\n'.format(n['titulo'], n['precio'],n['enlace'], "reservada" if n['reservada'] else "disponível") for n in offers
    ]
    html_body = "".join([str(item) for item in offers_html_array])

    html = """\
    <html>
    <body>
    """ + html_body +"""\
    </html>
    </body>
    """

    # Convert both parts to MIMEText objects and add them to the MIMEMultipart message
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    # Send Mail
    try:
        server.sendmail(
        cfg.username, cfg.receiver, message.as_string()
    )
        print("Email sent successfully.")
    except smtplib.SMTPException as e:
        print(f"SMTP Exception: {e}")

    server.quit()

def scrappeOffers(driver):
    '''Check all offers on website'''
    WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler")))
    accept_terms_button = driver.find_element("id", "onetrust-accept-btn-handler")
    if(accept_terms_button is not None):
        accept_terms_button.send_keys(Keys.RETURN)

    sleep(20)

    # Scroll down to load more content
    body = driver.find_element(By.TAG_NAME, 'body')
    for _ in range(3):  # Adjust the number of scrolls based on your needs
        body.send_keys(Keys.PAGE_DOWN)
        sleep(2)  # Adjust the sleep time based on your needs

    cards = driver.find_elements("css selector", '.ItemCardList__item')
    if(cards is not None):
        new_cards = []
        for e in cards:
            try:
                precio = e.find_element("class name", 'ItemCard__price').text
                titulo = e.find_element("class name", 'ItemCard__title').text
                link = e.get_attribute('href')
                #reservada
                reservada = False
                try:
                    reservada_element = e.find_element("class name", 'ItemCard__badge')
                    if(reservada_element is not None):
                        reservada = True
                except NoSuchElementException:
                    reservada = False
                new_cards.append({'titulo': titulo, 'precio': precio, 'enlace': link, 'reservada': reservada })
            except:
                pass
        return new_cards

def setupDriver():
    '''Setup chrome driver to scrape'''
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(cfg.OFFERS_URL)
    return driver

def checkHistory(current_offers):
    ''' Check local stored offers and only send the new ones'''
    new_offers= []
    if os.path.exists('offers.pickle'):
        with open('offers.pickle', 'rb') as f:
            data = pickle.load(f)
        for offer in current_offers:
            if offer not in data:
                data.append(offer)
                new_offers.append(offer)
    else:
        data = current_offers
        new_offers = current_offers
    with open('offers.pickle', 'wb') as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
    return new_offers
                     
if __name__=="__main__":

    driver= setupDriver()

    offers = scrappeOffers(driver)

    new_offers = checkHistory(offers)

    if new_offers:
        sendMail(new_offers)
    driver.quit()