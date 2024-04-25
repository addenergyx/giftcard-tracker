import requests

class GiftCardAPIService:
    def __init__(self, captcha_bypass):
        self.captcha_bypass = captcha_bypass
        self.api_url = "https://api.asdagiftcards.com/api/v1/balance"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:104.0) Gecko/20100101 Firefox/104.0",
            "Accept": "application/json, text/plain, */*",
        }

    def get_balance(self, card_number, pin):
        captcha_response = self.captcha_bypass.bypass()
        payload = {
            "number": card_number,
            "pin": pin,
            "recaptcha": captcha_response
        }

        response = requests.post(self.api_url, json=payload, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            if 'response_code' in data and data['response_code'] == '00':
                balance = float(data['new_balance'][:-2] + '.' + data['new_balance'][-2:])
                return balance
        return None