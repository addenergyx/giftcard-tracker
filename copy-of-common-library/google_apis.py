# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 19:43:42 2022

@author: david
"""
import logging
import pickle
import os
import datetime
from collections import namedtuple
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
# from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
import boto3

AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
WORKING_ENV = os.getenv('WORKING_ENV', 'DEV')

logger = logging.getLogger(__name__)


def create_service(client_secret_file, api_name, api_version, *scopes, prefix=''):
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]

    cred = None
    working_dir = '/tmp' if WORKING_ENV == 'PROD' else os.getcwd()
    logger.info({'working_dir': working_dir})
    token_dir = 'token files'
    pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}{prefix}.pickle'
    bucket = 'adoka-google-apis'

    s3 = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

    if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):

        try:
            # https://stackoverflow.com/questions/67088358/how-to-read-pickle-file-from-aws-s3-nested-directory
            s3_response_object = s3_client.get_object(Bucket=bucket, Key=token_dir + '/' + pickle_file)
            body_string = s3_response_object['Body'].read()
            cred = pickle.loads(body_string)

            logger.info(f'Credential object loaded from s3: {cred}')

            if cred.expired:
                cred.refresh(Request())

            if API_SERVICE_NAME == 'photoslibrary':
                # https://stackoverflow.com/questions/40154672/importerror-file-cache-is-unavailable-when-using-python-client-for-google-ser
                service = build(API_SERVICE_NAME, API_VERSION, credentials=cred,
                                # static_discovery=False
                                )  # Add static_discovery=False for photoslibrary api
            else:
                service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
            logger.info(f'{API_SERVICE_NAME} {API_VERSION} service created successfully')
            return service
        except Exception as e:
            logger.error(f'Failed to create service instance for {API_SERVICE_NAME}: {e}')
            return None

    ### Check if token dir exists first, if not, create the folder
    logger.info({'token_dir': os.path.join(working_dir, token_dir)})
    if not os.path.exists(os.path.join(working_dir, token_dir)):
        os.mkdir(os.path.join(working_dir, token_dir))

    if os.path.exists(os.path.join(working_dir, token_dir, pickle_file)):
        with open(os.path.join(working_dir, token_dir, pickle_file), 'rb') as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()

        with open(os.path.join(working_dir, token_dir, pickle_file), 'wb') as token:
            pickle.dump(cred, token)
            s3.Object(bucket, token_dir + '/' + pickle_file).put(Body=pickle.dumps(cred))

    # 			s3.upload_fileobj(token, bucket, token_dir+'/'+pickle_file)

    try:
        if API_SERVICE_NAME == 'photoslibrary':
            service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
            # static_discovery=False)  # Add static_discovery=False for photoslibrary api. Static_discovery no longer works
        else:
            service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)

        logger.info(f'{API_SERVICE_NAME} {API_VERSION} service created successfully')
        return service
    except Exception as e:
        logger.error(f'Failed to create service instance for {API_SERVICE_NAME}: {e}')
        os.remove(os.path.join(working_dir, token_dir, pickle_file))
        return None


def convert_to_RFC_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + 'Z'
    return dt


class GoogleSheetsHelper:
    # --> spreadsheets().batchUpdate()
    Paste_Type = namedtuple('_Paste_Type',
                            ('normal', 'value', 'format', 'without_borders',
                             'formula', 'date_validation', 'conditional_formatting')
                            )('PASTE_NORMAL', 'PASTE_VALUES', 'PASTE_FORMAT', 'PASTE_NO_BORDERS',
                              'PASTE_FORMULA', 'PASTE_DATA_VALIDATION', 'PASTE_CONDITIONAL_FORMATTING')

    Paste_Orientation = namedtuple('_Paste_Orientation', ('normal', 'transpose'))('NORMAL', 'TRANSPOSE')

    Merge_Type = namedtuple('_Merge_Type', ('merge_all', 'merge_columns', 'merge_rows')
                            )('MERGE_ALL', 'MERGE_COLUMNS', 'MERGE_ROWS')

    Delimiter_Type = namedtuple('_Delimiter_Type', ('comma', 'semicolon', 'period', 'space', 'custom', 'auto_detect')
                                )('COMMA', 'SEMICOLON', 'PERIOD', 'SPACE', 'CUSTOM', 'AUTODETECT')

    # --> Types
    Dimension = namedtuple('_Dimension', ('rows', 'columns'))('ROWS', 'COLUMNS')

    Value_Input_Option = namedtuple('_Value_Input_Option', ('raw', 'user_entered'))('RAW', 'USER_ENTERED')

    Value_Render_Option = namedtuple('_Value_Render_Option', ["formatted", "unformatted", "formula"]
                                     )("FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA")

    @staticmethod
    def define_cell_range(
            sheet_id,
            start_row_number=1, end_row_number=0,
            start_column_number=None, end_column_number=0):
        """GridRange object"""
        json_body = {
            'sheetId': sheet_id,
            'startRowIndex': start_row_number - 1,
            'endRowIndex': end_row_number,
            'startColumnIndex': start_column_number - 1,
            'endColumnIndex': end_column_number
        }
        return json_body

    @staticmethod
    def define_dimension_range(sheet_id, dimension, start_index, end_index):
        json_body = {
            'sheetId': sheet_id,
            'dimension': dimension,
            'startIndex': start_index,
            'endIndex': end_index
        }
        return json_body


class GoogleCalendarHelper:
    ...


class GoogleDriverHelper:
    ...


if __name__ == '__main__':
    g = GoogleSheetsHelper()
    print(g.Delimiter_Type)
