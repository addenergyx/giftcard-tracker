import http.client
import urllib
import os
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, notification_token, notification_user=os.getenv('NOTIFICATION_USER')):
        self.notification_token = notification_token
        self.notification_user = notification_user

    def push_notification(self, title, message, priority='0'):
        payload = {
            "token": self.notification_token,
            "user": self.notification_user,
            "title": title,
            "message": message,
            "url": "",
            "priority": priority,
            "html": 1
        }

        if priority == '2':
            payload.update({'retry': '30', 'expire': '10800'})

        # Create a new connection for each request
        conn = http.client.HTTPSConnection("api.pushover.net:443")

        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode(payload), {"Content-type": "application/x-www-form-urlencoded"})

        logger.info(f'Push notification sent: {title} - {message}')

        # Get the response
        response = conn.getresponse()
        # Optionally, you can process the response or return it
        conn.close()

        return response
