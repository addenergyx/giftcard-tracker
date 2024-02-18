# -*- coding: utf-8 -*-

import boto3
import os

AWS_DEFAULT_REGION = "eu-west-1"
WORKING_ENV = os.getenv('WORKING_ENV', 'DEV')


def get_session():

    if WORKING_ENV == 'PROD':
        session = boto3.Session(
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            aws_session_token=os.environ["AWS_SESSION_TOKEN"]
        )
    else:
        from dotenv import load_dotenv
        load_dotenv(verbose=True, override=True)

        session = boto3.Session(
            aws_access_key_id=os.environ["AWS_ACCESS_KEY"],
            aws_secret_access_key=os.environ["AWS_SECRET_KEY"],
        )
    return session

def connect_to_dynamodb(table_name):

    dynamodb = get_session().resource('dynamodb', region_name=AWS_DEFAULT_REGION)
    
    return dynamodb.Table(table_name)    

def connect_to_s3():
    return get_session().resource('s3', region_name=AWS_DEFAULT_REGION)

def connect_to_sqs_queue(queue_name):
    return get_session().resource('sqs').get_queue_by_name(QueueName=queue_name)

def queue_active(queue):

    if int(queue.attributes["ApproximateNumberOfMessages"]) > 0  and queue.attributes["ApproximateNumberOfMessagesNotVisible"] == '0':
        return True
    else:
        return False
