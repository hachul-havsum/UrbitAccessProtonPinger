#!/usr/bin/env python3
import click
import getpass, sys
import requests
import shelve

HEADERS = {'Content-Type': 'application/json'}
PAYLOAD = '{ "source": { "dojo": "+code" }, "sink" : {"stdout": null} }'
URL = "http://localhost:%d"

def get_access_code(port):
    r = requests.get(URL % port, headers=HEADERS,data=PAYLOAD)

    if r.status_code == 200:
        code = r.text
        code = code.replace('"', "")
        code = code.replace("\\n", "")
        return code
    else:
        return "Failed with code %d" % r.status_code


def email_access_code(email_addr, pw, code, port):
    # From Stackoverflow:
    # https://stackoverflow.com/questions/56330521/sending-an-email-with-python-from-a-protonmail-account-smtp-library

    import smtplib 
    try:
        from email.MIMEMultipart import MIMEMultipart 
    except:
        from email.mime.multipart import MIMEMultipart

    try:    
        from email.MIMEText import MIMEText
    except:
        from email.mime.text import MIMEText

    msg = MIMEMultipart()
    msg['From'] = email_addr
    msg['To'] = email_addr
    msg['Subject'] = 'Urbit Status'
    message = 'Urbit Access Code:\n%s' % code
    msg.attach(MIMEText(message))
    mailserver = smtplib.SMTP('localhost',port)
    mailserver.login(email_addr, pw)
    mailserver.sendmail(email_addr,email_addr,msg.as_string())
    mailserver.quit()
    return

@click.command()
@click.option("--cache_file", required=True, help="Filename for cache storage")
@click.option("--email", prompt=True, required=True, help="Email address to send/recv")
@click.option("--password", default=None, help="Proton SMTP Bridge Password (omit to prompt)")
@click.option("--urbit_port", default=12321, help="Urbit loopback port (defaults to 12321)")
@click.option("--smtp_port", default=1025, help="Proton SMTP Bridge port (defaults to 1025)")
def UrbitAccessProtonPinger(cache_file, email, password, urbit_port, smtp_port):
    cache = shelve.open(cache_file)    
    old_code = cache.get("code", None)

    new_code = get_access_code(urbit_port)
    
    if new_code != old_code:
        cache["code"] = new_code
        cache.close()

        if password == None:
            print("Email ", end="")
            sys.stdout.flush()
            password = getpass.getpass()

        email_access_code(email, password, new_code, smtp_port)
    else:
        cache.close()

if __name__ == "__main__":
    UrbitAccessProtonPinger()
