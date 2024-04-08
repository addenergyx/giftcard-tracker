import boto3
import json
from boto3.dynamodb.conditions import Attr

from dotenv import load_dotenv

from utils import setup_logging

load_dotenv('.env', verbose=True, override=True)

from common_shared_library import AWSConnector


def lambda_handler(event, context):
    logger = setup_logging()

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

    # Create an SQS client
    sqs = boto3.client('sqs')

    # The URL for your SQS queue (you can get this from the AWS console)
    queue_url = 'https://sqs.eu-west-1.amazonaws.com/334010140999/GiftcardQueue'

    for task in giftcard_tasks:
        # Convert the task to a JSON string to send as the message body

        task.pop('balance', None)

        message_body = json.dumps(task)

        # Send the message to the SQS queue
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )

        # Print out the response
        logger.info(f"Giftcard {task['card_id']} added to the queue")

    return {
        'statusCode': 200,
        'body': json.dumps('Giftcards added to the queue')
    }