import json
import os
import sys
from decimal import Decimal
import logging
import requests
from common_shared_library import CaptchaBypass, lambda_docker_selenium
from common_shared_library.driver_manager import DriverManager

logger = logging.getLogger(__name__)


def get_balancer(card_number, pin):
    BALANCE_CHECKER_URL = "https://www.asdagiftcards.com/balance-check"
    API_URL = "https://api.asdagiftcards.com/api/v1/balance"
    PUBLIC_SITEKEY = '6LcGYtkZAAAAAHu9BgC-ON7jeraLq5Tgv3vFQzZZ'

    g_response = CaptchaBypass(PUBLIC_SITEKEY, BALANCE_CHECKER_URL).bypass()

    payload = {
        "number": card_number,
        "pin": pin,
        "recaptcha": g_response
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:104.0) Gecko/20100101 Firefox/104.0",
        "Accept": "application/json, text/plain, */*",
    }

    return requests.request("POST", API_URL, json=payload, headers=headers).json()


def add_giftcards_to_table(data, giftcards_table) -> None:
    dic_ = [{'card_id': x[0], 'balance': x[1], 'link': x[2], 'pin': x[3]} for x in data]

    logger.info(f"Adding giftcards to giftcard table: {dic_}")

    # https://github.com/boto/boto3/issues/2584
    with giftcards_table.batch_writer(overwrite_by_pkeys=['card_id']) as batch:
        for row in dic_:
            giftcard_dic = json.loads(json.dumps(row), parse_float=Decimal)
            logger.info(f"Adding giftcard {giftcard_dic['card_id']} in giftcard table")
            batch.put_item(Item=giftcard_dic)

    # # https://github.com/boto/boto3/issues/2584
    # with giftcards_table.batch_writer(overwrite_by_pkeys=['card_id']) as batch:
    #     for row in dic_:
    #         giftcard_dic = json.loads(json.dumps(row), parse_float=Decimal)
    #         card_id = giftcard_dic['card_id']
    #
    #         # Check if the item exists and fetch its current data
    #         existing_item = giftcards_table.get_item(Key={'card_id': card_id}).get('Item')
    #
    #         if existing_item is None or existing_item != giftcard_dic:
    #             logger.info(f"Updated details {card_id} in giftcard table")
    #
    #             '''The batch_writer context manager will automatically group the put_item operations into batches and send them to DynamoDB.
    #             The condition check (if existing_item is None or existing_item != giftcard_dic) will determine whether
    #             the put_item operation should be added to the batch or not.'''
    #             batch.put_item(Item=giftcard_dic)
    #         else:
    #             logger.info(f"No changes for {card_id}, skipping update")


def money_format(value, currency_symbol='£'):
    return f"{currency_symbol}{value:.2f}"


def driver_selection():
    if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        driver = lambda_docker_selenium.get_driver()
        directory = '/tmp'
    else:
        driver_manager = DriverManager()
        driver = driver_manager.get_driver(headless=True)
        directory = os.path.join(os.getcwd(), 'images')

    return driver, directory

def setup_logging():
    logger = logging.getLogger()
    for h in logger.handlers:
        logger.removeHandler(h)

    h = logging.StreamHandler(sys.stdout)

    # use whatever format you want here
    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    h.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

    return logger