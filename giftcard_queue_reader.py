import asyncio
import json
import os
import boto3
from boto3.dynamodb.conditions import Attr

from dotenv import load_dotenv

from GiftCard import GiftCard
from GiftCardAPIService import GiftCardAPIService

load_dotenv('.env', verbose=True, override=True)

from utils import add_giftcards_to_table, money_format, setup_logging
from common_shared_library import NotificationManager, AWSConnector, CaptchaBypass
from common_shared_library.google_photos_upload import get_media_items_id, remove_media

logger = setup_logging()


def is_last_batch(queue_attributes, records_count, batch_item_failures):
    # Check if there are no messages left in the queue and no messages being processed elsewhere
    if (int(queue_attributes["ApproximateNumberOfMessages"]) == 0 and
            int(queue_attributes["ApproximateNumberOfMessagesNotVisible"]) == records_count and
            len(batch_item_failures) == 0):
        return True
    return False


def handle_zero_balance(giftcard: GiftCard, notification_manager: NotificationManager):
    img_filename = f'giftcard_{giftcard.card_number}.png'
    media_to_delete = get_media_items_id(filter_=[img_filename])
    notification_manager.push_notification(
        "Deleting Giftcard from Photos Gallery",
        f"Deleting giftcard {giftcard.card_number} from photos gallery as balance is {giftcard.balance}"
    )

    # Make note in description to delete giftcard from main photos gallery
    request_body = {
        "description": "Balance is 0. Delete this giftcard"
    }

    if media_to_delete:
        remove_media(media_to_delete, request_body=request_body)
        logger.info(f"Giftcard {giftcard.card_number} balance is 0. Deleting from photos gallery...")


def lambda_handler(event, context):
    batch_item_failures = []
    data = []

    # driver, directory = driver_selection()
    notification_manager = NotificationManager()

    MAX_RETRIES = 5

    for record in event['Records']:

        try:

            message_body = json.loads(record['body'])

            gift_card = GiftCard(message_body['card_id'], message_body['pin'])
            captcha_bypass = CaptchaBypass(sitekey="6LcGYtkZAAAAAHu9BgC-ON7jeraLq5Tgv3vFQzZZ",
                                           url="https://www.asdagiftcards.com/balance-check")
            api_service = GiftCardAPIService(captcha_bypass)

            for attempt in range(MAX_RETRIES):
                balance = api_service.get_balance(gift_card.card_number, gift_card.pin)
                if balance is not None:
                    gift_card.update_balance(balance)
                    logger.info(f"Balance successfully retrieved for card {gift_card.card_number}")
                    break
                else:
                    logger.error(
                        f"Attempt {attempt + 1}: Failed to get balance for card {gift_card.card_number}. Retrying...")
            else:
                # Only executed if the loop completes without a 'break'
                logger.error(
                    f"Failed to get balance for card {gift_card.card_number} after {MAX_RETRIES} attempts. Skipping...")
                data.append([gift_card.card_number, '-', message_body['link'], message_body['pin']])
                notification_manager.push_notification(
                    title='Giftcard Balance Update Failure',
                    message=f"Failed to get balance for card {gift_card.card_number}. Skipping..."
                )
                continue  # Skip further processing

            # balance = float(response['new_balance']) / 100

            if balance is not None and balance == 0:
                handle_zero_balance(gift_card,
                                    notification_manager)  # Assuming this is a function to handle zero balance scenario
            elif balance is not None:
                notification_manager.push_notification(
                    title='Giftcard Balance',
                    message=f'Your giftcard {gift_card.card_number} balance is {money_format(balance)}',
                )
                logger.info(f"Giftcard {gift_card.card_number} balance updated to {balance}!")

            data.append([gift_card.card_number, balance, message_body['link'], message_body['pin']])


        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            logger.error(f"Failed to process message {record['messageId']}. Error: {e}")

    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
    AWS_DEFAULT_REGION = "eu-west-1"

    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_DEFAULT_REGION
    )

    giftcards_table = dynamodb.Table('giftcards')

    add_giftcards_to_table(data, giftcards_table)

    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='GiftcardQueue')

    # if last lambda batch
    queue_attributes = queue.attributes
    last_batch = is_last_batch(queue_attributes, len(event['Records']), batch_item_failures)
    if last_batch:

        aws_manager = AWSConnector()

        table = aws_manager.connect_to_dynamodb("giftcards")

        response = table.scan(
            FilterExpression=Attr('balance').gt(0)
        )

        # Extract items with balance greater than 0
        giftcards = response['Items']

        # Since `scan` reads up to the maximum number of items set (default is 1MB of data),
        # you must handle pagination if the entire result set requires more than 1MB
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('balance').gt(0),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            giftcards.extend(response['Items'])

        total = sum([x['balance'] for x in giftcards])

        notification_manager.push_notification(
            title='Giftcard Balance',
            message=f'Total aggregated balance: {money_format(total)}',
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                "body": {
                    'message': 'Giftcard lambdas invoked successfully',
                    'total_balance': float(total),
                }
            }, indent=4)
        }

    return {
        'statusCode': 200,
        "batchItemFailures": batch_item_failures,
        'body': json.dumps('Giftcard balance(s) updated successfully!'),
    }


if __name__ == '__main__':
    event = {'Records': [

        {'messageId': '695f1cd2-82ca-4aa7-b254-335e7fe29320',
         'body': '{"link": "https://www.wgiftcard.co/pbt/9/40937011/6316759248450891/4612/15.00/MA/a92928fe39ed752dfc13a37ea191d8c90a95419d", '
                 '"card_id": "6316759248450891", "pin": "xxxx"}',
         'attributes': {'ApproximateReceiveCount': '1', 'SentTimestamp': '1712596957113',
                        'SenderId': 'AIDAU3REOJFDV64UUHGJG', 'ApproximateFirstReceiveTimestamp': '1712596963616'},
         'messageAttributes': {}, 'md5OfBody': '4238c9687fa4b44da6f0f6f6a8730630', 'eventSource': 'aws:sqs',
         'eventSourceARN': 'arn:aws:sqs:eu-west-1:334010140999:GiftcardQueue', 'awsRegion': 'eu-west-1'},

        {'messageId': 'de08455e-b92a-472e-b424-cd748e7d6327',
         'body': '{"link": "https://www.wgiftcard.co/pbt/9/40816731/6316758295019599/4127/5.00/MA/ce44319c9166d26b4bb658462376fe34bb86c118", '
                 '"card_id": "6316758295019599", "pin": "xxxx"}',
         'attributes': {'ApproximateReceiveCount': '1', 'SentTimestamp': '1712596957205',
                        'SenderId': 'AIDAU3REOJFDV64UUHGJG', 'ApproximateFirstReceiveTimestamp': '1712596963616'},
         'messageAttributes': {}, 'md5OfBody': 'b035cff3a64bc56ac274a4b54e92d98a', 'eventSource': 'aws:sqs',
         'eventSourceARN': 'arn:aws:sqs:eu-west-1:334010140999:GiftcardQueue', 'awsRegion': 'eu-west-1'},

        {'messageId': '8fcf2f66-da34-40d9-a993-7b7bce2e13e1',
         'body': '{"link": "https://www.wgiftcard.co/pbt/9/40769611/6316757887309413/4567/5.00/MA/17e279b433495b048e5f4aea25deff1489140430", '
                 '"card_id": "6316757887309413", "pin": "xxxx"}',
         'attributes': {'ApproximateReceiveCount': '1', 'SentTimestamp': '1712596957238',
                        'SenderId': 'AIDAU3REOJFDV64UUHGJG', 'ApproximateFirstReceiveTimestamp': '1712596963616'},
         'messageAttributes': {}, 'md5OfBody': '956a5572ec39eaf2e1c00c7a58221f37', 'eventSource': 'aws:sqs',
         'eventSourceARN': 'arn:aws:sqs:eu-west-1:334010140999:GiftcardQueue', 'awsRegion': 'eu-west-1'},

        {'messageId': '8fcf2f66-da34-40d9-a993-7b7bce2e13e2',
         'body': '{"link": "https://www.wgiftcard.co/pbt/9/40769611/6316757887309413/4567/5.00/MA/xxxxxxxx", '
                 '"card_id": "6315757924074551", "pin": "xxxx"}',
         'attributes': {'ApproximateReceiveCount': '1', 'SentTimestamp': '1712596957238',
                        'SenderId': 'AIDAU3REOJFDV64UUHGJG', 'ApproximateFirstReceiveTimestamp': '1712596963616'},
         'messageAttributes': {}, 'md5OfBody': '956a5572ec39eaf2e1c00c7a58221f37', 'eventSource': 'aws:sqs',
         'eventSourceARN': 'arn:aws:sqs:eu-west-1:334010140999:GiftcardQueue', 'awsRegion': 'eu-west-1'}
    ]}

    # async def run():
    #     tasks = [asyncio.create_task(perky(perk)) for perk in perks]
    #     results = await asyncio.gather(*tasks)

    print(lambda_handler(event, None))
