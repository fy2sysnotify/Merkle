import smtplib
from email.message import EmailMessage


text_file = 'textfile.txt'

with open(text_file) as fp:
    msg = EmailMessage()
    msg.set_content(fp.read())

# me == the sender's email address
# you == the recipient's email address
msg['Subject'] = f'The contents of {text_file}'
msg['From'] = 'konstantin.yanev@isobar.com'
msg['To'] = 'kosyoyanev@gmail.com'

# Send the message via our own SMTP server.
s = smtplib.SMTP('localhost','25')
s.send_message(msg)
s.quit()