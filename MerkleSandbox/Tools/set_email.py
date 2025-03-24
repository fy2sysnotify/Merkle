import os
import smtplib
import constants as const
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


def send_email(recipient,
               subject_of_email,
               email_message,
               attachment_location=''):
    email_sender = const.ods_email

    email = MIMEMultipart()
    email_cc = const.my_business_email
    email['From'] = const.ods_email
    email['To'] = recipient
    email['Subject'] = subject_of_email

    email.attach(MIMEText(email_message, 'html'))

    if attachment_location != '':
        config_attachment(attachment_location, email)
    try:
        config_connection(email, email_sender, recipient, email_cc)
    except Exception as e:
        print(f'SMPT server connection error. Failed to send email. {e}')


def config_connection(email, email_sender, recipient, email_cc):
    server = smtplib.SMTP(const.smtp_server, const.smtp_port)
    server.ehlo()
    server.starttls()
    server.login(const.ods_email, const.ods_pass)
    text = email.as_string()
    server.sendmail(email_sender, recipient.split(',') + email_cc.split(','), text)
    print('email sent')
    server.quit()


def config_attachment(attachment_location, email):
    filename = os.path.basename(attachment_location)
    attachment = open(attachment_location, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',
                    "attachment; filename= %s" % filename)
    email.attach(part)
