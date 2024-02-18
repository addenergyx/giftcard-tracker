import http.client, urllib
import os

from dotenv import load_dotenv
load_dotenv(verbose=True, override=True)

NOTIFICATION_USER = os.getenv('NOTIFICATION_USER')

def push_notification(NOTIFICATION_TOKEN, title, message, priority: str='0' ):

    # create connection
    conn = http.client.HTTPSConnection("api.pushover.net:443")

    payload = {
        "token": NOTIFICATION_TOKEN,
        "user": NOTIFICATION_USER,
        "title": title,
        "message": message,
        "url": "",
        "priority": priority,
        "html": 1
      }

    if priority == '2':
        payload = {**payload, **{'retry':'30', 'expire': '10800'}}

    # make POST request to send message
    conn.request("POST", "/1/messages.json",
      urllib.parse.urlencode(payload), { "Content-type": "application/x-www-form-urlencoded" })

    # get response
    conn.getresponse()
