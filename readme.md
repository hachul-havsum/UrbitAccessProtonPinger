
## Urbit Access Proton Pinger

The purpose of the UrbitAccessProtonPinger is to notify an Urbit ship owner of the Landscape access code and base hash via a secure method.

    hachul-havsum@urbit:~/urbit/git/UrbitAccessProtonPinger$ ./UrbitAccessProtonPinger.py --help
    Usage: UrbitAccessProtonPinger.py [OPTIONS]

    Options:
      --cache_file TEXT     Filename for cache storage  [required]
      --email TEXT          Email address to send/recv  [required]
      --password TEXT       Proton SMTP Bridge Password (omit to prompt)
      --urbit_port INTEGER  Urbit loopback port (defaults to 12321)
      --smtp_port INTEGER   Proton SMTP Bridge port (defaults to 1025)
      --help                Show this message and exit.


The pinger runs as a `cron` job and periodically queries the urbit `dojo` via the loopback mechanism to obtain the current value of the urbit information (access code and base hash). By use of a local hashed caching mechanism, only when the values have changed will the user be notified of the new values.

The notification method is to send an encrypted email using a single protonmail.com email address as the sender and receiver.

Note: this solution requires the [ProtonMail Bridge Software](https://protonmail.com/bridge/install) installed on the same node as the Urbit ship and this Pinger utility.

To use the pinger, follow these steps:
1) Clone this repo on your Urbit ship node
2) If you don't already have one, create a Protonmail.com email account. Install its apps on the mobile devices you plan on receiving urbit pinger alerts
3) Install the email bridge from  https://protonmail.com/bridge/install
4) Run the ProtonMail bridge and add your ProtonMail account to it. Leave it running
5) Add the pinger as a `cron` job. The following is a quick example of one way to accomplish this:
     1) From a terminal window, use the command `crontab -e`. Note you don't have to be superuser to edit the crontab file for your userid.
     2) Add a job line for the pinger such as this one, that checks every 10 minutes for a change in status:

> 0,10,20,30,40,50 * * * * /home/user/urbit/git/UrbitAccessProtonPinger/UrbitAccessProtonPinger.py \\
>  --cache_file ~/.urbit_pinger --email addr@protonmail.com --password bridge_smtp_pw

Remember: the `password` and  `smtp_port` arguments are the password and port from the ProtonMail SMTP Bridge utility.