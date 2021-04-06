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
    @staticmethod
    def _cleanup(input):
        return input

    def process(self, port):
        r = requests.get(URL % port, headers=HEADERS,data=PAYLOAD % self._query)
        result = []
        if r.status_code == 200:
            for regex in self._regex:
                item = self._cleanup(regex.findall(r.text)[0])
                result.append(item)
                print("Found:", item)
        return result


class AccessCode(UrbitQuery):
    _query = "+code"
    _regex = (re.compile(r'"((?:[a-z]{6}-){3}[a-z]{6})\\n"'),)

class BaseHashShipName(UrbitQuery):
    _query = "+trouble"    
    _regex = (re.compile(r'%base-hash ~\[[0-9A-Za-z]{1,4}\.(?:[0-9A-Za-z]{5}\.){9}([0-9A-Za-z]{5})\]'),
              re.compile(r'%our\s*ship=(~[a-z]{6}(?:(?:-[a-z]{6}-[a-z]{6}){0,1}-[a-z]{6}(?:--[a-z]{6}-[a-z]{6}-[a-z]{6}-[a-z]{6}){0,1}){0,1})'))

class Tally(UrbitQuery):
    _query = "+tally |"
    _regex = (re.compile(r'"\\n([\s\S]+)\\n"'),)
    _cleanup = staticmethod(lambda x: x.replace(r"\n", "\n"))

URBIT_QUERIES = (AccessCode, BaseHashShipName, Tally)

def get_urbit_info(port):
    results = []
    for query in URBIT_QUERIES:
        results.extend(query().process(port))
    return tuple(results)

def email_access_code(email_addr, pw, code, hsh, name, tally, port):
    # From Stackoverflow:
    # https://stackoverflow.com/questions/56330521/sending-an-email-with-python-from-a-protonmail-account-smtp-library

    import smtplib 
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart()
    msg['From'] = email_addr
    msg['To'] = email_addr
    msg['Subject'] = 'Urbit Status (%s)' % name
    message = 'Urbit Ship Name:\n%s\n\nUrbit Access Code:\n%s\n\nUrbit Hash:\n%s\n\nUrbit Tally:\n%s' % (name, code, hsh, tally)
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
    old_name_hash = cache.get("name_hash", None)

    # get the new values
    new_code, new_hsh, new_name, tally = get_urbit_info(urbit_port)

    # create their hashes
    new_code_hash = hashlib.md5(new_code.encode("utf-8")).hexdigest()
    new_hsh_hash = hashlib.md5(new_hsh.encode("utf-8")).hexdigest()
    new_name_hash = hashlib.md5(new_name.encode("utf-8")).hexdigest()

    # if either of them changed, update the cache and send the alert
    if new_code_hash != old_code_hash or \
       new_hsh_hash != old_hsh_hash  or  \
       new_name_hash != old_name_hash:
        cache["code_hash"] = new_code_hash
        cache["hsh_hash"] = new_hsh_hash
        cache["name_hash"] = new_name_hash 
        cache.close()

        if password == None:
            print("Email ", end="")
            sys.stdout.flush()
            password = getpass.getpass()

        email_access_code(email, password, new_code, new_hsh, new_name, tally, smtp_port)
    else:
        cache.close()

if __name__ == "__main__":
    UrbitAccessProtonPinger()
