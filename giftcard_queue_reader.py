import json
import os
import boto3
from boto3.dynamodb.conditions import Attr

from dotenv import load_dotenv

load_dotenv('.env', verbose=True, override=True)

from utils import get_balancer, add_giftcards_to_table, money_format, setup_logging
from common_shared_library import NotificationManager, AWSConnector
from common_shared_library.google_photos_upload import get_media_items_id, remove_media


def lambda_handler(event, context):
    batch_item_failures = []
    sqs_batch_response = {}
    data = []

    logger = setup_logging()
    # driver, directory = driver_selection()
    notification_manager = NotificationManager()

    for record in event['Records']:

        try:

            message_body = json.loads(record['body'])
            card_id = message_body['card_id']
            response = {}

            x = 0
            while x < 6:

                response = get_balancer(card_id, message_body['pin'])
                if 'response_code' in response and response['response_code'] == '00':
                    logger.info(f"Response from balance checker: {response}")
                    break
                else:
                    logger.error(f"Failed to get balance for card {card_id}. Retrying...")
                    x += 1

                if x == 5:
                    logger.error(f"Failed to get balance for card {card_id}. Skipping...")
                    data.append([card_id, '-', message_body['link'], message_body['pin']])
                    notification_manager.push_notification(
                        title='Giftcard Balance Updated',
                        message=f"Failed to get balance for card {card_id}. Skipping...",
                    )

            if x == 5:
                continue

            balance = float(response['new_balance']) / 100

            if balance == 0:
                img_filename = f'giftcard_{card_id}.png'
                media_to_delete = get_media_items_id(filter_=[img_filename])
                notification_manager.push_notification(
                    "Deleting Giftcard from Photos Gallery",
                    f"Deleting giftcard {card_id} from photos gallery as balance is {balance}"
                )

                # Make note in description to delete giftcard from main photos gallery
                request_body = {
                    "description": "Balance is 0. Delete this giftcard"
                }

                if media_to_delete:
                    remove_media(media_to_delete, request_body=request_body)
                    logger.info(f"Giftcard {card_id} balance is 0. Deleting from photos gallery...")

            else:
                notification_manager.push_notification(
                    title='Giftcard Balance',
                    message=f'Your giftcard {card_id} balance is {money_format(balance)}',
                )
                logger.info(f"Giftcard {card_id} balance updated to {balance}!")

            data.append([card_id, balance, message_body['link'], message_body['pin']])

        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures

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
    if int(queue.attributes["ApproximateNumberOfMessages"]) == 0 and queue.attributes["ApproximateNumberOfMessagesNotVisible"] == len(event['Records']):

        aws_manager = AWSConnector()

        table = aws_manager.connect_to_dynamodb("giftcards")

        response = table.scan(
            FilterExpression=Attr('balance').gt(0)
        )

        # Extract items with balance greater than 0
        giftcard_tasks = response['Items']

        # Since `scan` reads up to the maximum number of items set (default is 1MB of data),
        # you must handle pagination if the entire result set requires more than 1MB
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('balance').gt(0),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            giftcard_tasks.extend(response['Items'])

        total = sum([x['balance'] for x in giftcard_tasks])

        return {
            'statusCode': 200,
            'body': json.dumps(f'Giftcard balance(s) updated successfully! Total balance: {money_format(total)}')
        }


    return {
        'statusCode': 200,
        'body': json.dumps('Giftcard balance(s) updated successfully!')
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

    print(lambda_handler(event, None))
