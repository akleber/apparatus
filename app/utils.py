from app import app, mail, get_db
from threading import Thread
from flask_mail import Message
import uuid


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, text_body, html_body):
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


def add_user(firstName: str, familyName: str, mail: str) -> int:
    user_data = {
        "firstName": firstName,
        "familyName": familyName,
        "mail": mail,
        "mailVerificationToken": str(uuid.uuid4()),
        "gdprToken": str(uuid.uuid4()),
    }
    sql = """INSERT INTO user (firstName, familyName, mail, mailVerificationToken, gdprToken) 
             VALUES (:firstName, :familyName, :mail, :mailVerificationToken, :gdprToken) RETURNING userID;"""
    cur = get_db().execute(sql, user_data)
    userID = cur.lastrowid
    return userID, user_data
