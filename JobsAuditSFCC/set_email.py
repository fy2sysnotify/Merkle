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
    html_table: object,
    email_cc: str = '',
    attachment_location: str = ''
) -> None:

    """Send an email with optional attachment.

    This function sends an email to the specified recipient(s) with an optional attachment and HTML content.

    :param email_recipient: Email address of the recipient(s). Multiple emails must be provided as a single string, separated by commas.
    :type email_recipient: str

    :param email_subject: Subject line of the email.
    :type email_subject: str

    :param email_message: Plain text message of the email.
    :type email_message: str

    :param html_table: HTML content to be appended to the email body.
    :type html_table: object

    :param email_cc: Email addresses to be included in the CC field. Defaults to an empty string.
    :type email_cc: str, optional

    :param attachment_location: File path of the attachment. Defaults to an empty string.
    :type attachment_location: str, optional

    :return: None
    """

    email = MIMEMultipart('alternative')
    email['From'] = config('ODS_EMAIL', default='')
    email['To'] = email_recipient
    email['Cc'] = email_cc
    email['Subject'] = email_subject

    text_content = email_message
    html_content = "<html><body>{}</body></html>".format(email_message + str(html_table))

    text_part = MIMEText(text_content, "plain")
    html_part = MIMEText(html_content, "html")
    email.attach(text_part)
    email.attach(html_part)

    if attachment_location:
        filename = os.path.basename(attachment_location)
        with open(attachment_location, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {filename}")
            email.attach(part)

    try:
        server = smtplib.SMTP(config('SMTP_SERVER', default=''), config('SMTP_PORT', default=''))
        server.ehlo()
        server.starttls()
        server.login(config('ODS_EMAIL', default=''), config('ODS_PASS', default=''))
        text = email.as_string()
        recipients = email_recipient.split(',') + email_cc.split(',')
        server.sendmail(config('ODS_EMAIL', default=''), recipients, text)
        print('email sent')
        server.quit()
    except Exception as e:
        print(f'SMPT server connection error. Failed to send email. {e}')
