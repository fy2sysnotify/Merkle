import os
import smtplib
from decouple import config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


def send_email(
        email_recipient: str,
        email_subject: str,
        email_message: str,
        attachment_location: str,
        email_cc: str = '') -> None:
    """
    Sends an email with the specified subject and message to the given recipient.

    :param: email_recipient: The email address of the recipient.
            Multiple emails must be divided by comma "," in a single string
    :param: email_subject: The subject of the email.
    :param: email_message: The body of the email, in HTML format.
    :param: email_cc: Optional email address of the recipient in CC.
            Multiple emails must be divided by comma "," in a single string
    :param: attachment_location: The file path of an optional attachment.
    :return: None
    """
    email = MIMEMultipart()
    email['From'] = config('NOTIFICATION_EMAIL')
    email['To'] = email_recipient
    email['Cc'] = email_cc
    email['Subject'] = email_subject

    email.attach(MIMEText(email_message, 'html'))

    if attachment_location:
        filename = os.path.basename(attachment_location)
        with open(attachment_location, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {filename}")
            email.attach(part)

    try:
        server = smtplib.SMTP(config('SMTP_SERVER'), config('SMTP_PORT'))
        server.ehlo()
        server.starttls()
        server.login(config('NOTIFICATION_EMAIL'), config('EMAIL_PASS'))
        text = email.as_string()
        recipients = email_recipient.split(',') + email_cc.split(',')
        server.sendmail(config('NOTIFICATION_EMAIL'), recipients, text)
        print('email sent')
        server.quit()
    except Exception as e:
        print(f'SMPT server connection error. Failed to send email. {e}')
