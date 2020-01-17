import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr


# function to send confirmation email.
def send_mail(email, name):
    port = 465
    with open('key.txt', 'r') as file:
        password = file.readlines()[1].rstrip()
    sender_mail = "chat@grodvidar.se"
    receiver_mail = email

    message = MIMEMultipart("alternative")
    message['Subject'] = "Registration"
    message['From'] = formataddr((str(Header('Haxr-Chat', 'utf-8')), sender_mail))
    message['To'] = receiver_mail

    text = f"""\
        Hello {name}!
        Welcome to Haxr-Chat! ☺
        Best regards,
        The Haxr-Chat-group"""
    html = f"""\
        <html>
          <body>
            <p>Hello {name}!<br>
               Welcome to Haxr-Chat! ☺<br>
               <br>
               Best regards,<br>
               The Haxr-Chat-group
            </p>
          </body>
        </html>
        """

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("cpsrv49.misshosting.com", port, context=context) as server:
        server.login(sender_mail, password)
        server.sendmail(sender_mail, receiver_mail, message.as_string())


if __name__ == '__main__':
    send_to = input("enter mail to send to")
    send_name = input("enter receivers name")
    send_mail(send_to, send_name)
