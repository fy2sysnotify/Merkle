import os
import smtplib
import imghdr
from email.message import EmailMessage

EMAIL_ADDRESS = os.environ.get('sys2_user')
EMAIL_PASSWORD = os.environ.get('sys2_pass')

# Send to single email
to_receiver = 'kosyoyanev@gmail.com'

# Send to list of contacts
# contacts = ['kosyoyanev@gmail.com', 'kosyoyanev2@gmail.com', 'kosyoyanev3@gmail.com', 'p4r4m0un7@gmail.com']

msg = EmailMessage()
msg['Subject'] = 'fy2sys notify LOCAL'
msg['From'] = EMAIL_ADDRESS
msg['To'] = to_receiver  #', '.join(contacts)
msg.set_content('Ready with the calculations.')

# Use to attach files
# attached_file = ['file1', 'file2', 'etc']
#
# for file in attached_file:
#     with open(file, 'rb') as f:
#         file_data = f.read()
#         file_name = f.name
#
#     msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    smtp.send_message(msg)