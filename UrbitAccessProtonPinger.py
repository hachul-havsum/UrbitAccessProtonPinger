#!/usr/bin/env python3
import click
import getpass, sys
import requests
import shelve
import hashlib
import re

HEADERS = {'Content-Type': 'application/json'}
PAYLOAD = '{ "source": { "dojo": "%s" }, "sink" : {"stdout": null} }'
URL = "http://localhost:%d"

class UrbitQuery(object):
    def process(self, port):
        r = requests.get(URL % port, headers=HEADERS,data=PAYLOAD % self._query)
        result = None
        if r.status_code == 200:
            result = self._regex.findall(r.text)[0]
        return result

class AccessCode(UrbitQuery):
    _regex = re.compile(r'"((?:[a-z]{6}-){3}[a-z]{6})\\n"')
    _query = "+code"

class BaseHash(UrbitQuery):
    _regex = re.compile(r'%base-hash ~\[[0-9A-Za-z]{4}\.(?:[0-9A-Za-z]{5}\.){9}([0-9A-Za-z]{5})\]')
    _query = "+trouble"

URBIT_QUERIES = (AccessCode, BaseHash)

def get_urbit_info(port):
    return tuple([fn().process(port) for fn in URBIT_QUERIES])

def email_access_code(email_addr, pw, code, hsh, port):
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
    message = 'Urbit Access Code:\n%s\n\nUrbit Hash:\n%s\n' % (code, hsh)
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
    # Open our cache of previously polled values
    cache = shelve.open(cache_file)

    # read the old values
    old_code_hash = cache.get("code_hash", None)
    old_hsh_hash = cache.get("hsh_hash", None)

    # get the new values and create their hashes
    new_code, new_hsh = get_urbit_info(urbit_port)
    new_code_hash = hashlib.md5(new_code.encode("utf-8")).hexdigest()
    new_hsh_hash = hashlib.md5(new_hsh.encode("utf-8")).hexdigest()

    # if either of them changed, update the cache and send the alert
    if new_code_hash != old_code_hash or new_hsh_hash != old_hsh_hash:
        cache["code_hash"] = new_code_hash
        cache["hsh_hash"] = new_hsh_hash
        cache.close()

        if password == None:
            print("Email ", end="")
            sys.stdout.flush()
            password = getpass.getpass()

        email_access_code(email, password, new_code, new_hsh, smtp_port)
    else:
        cache.close()

if __name__ == "__main__":
    UrbitAccessProtonPinger()
