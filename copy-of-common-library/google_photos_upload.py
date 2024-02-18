# -*- coding: utf-8 -*-
"""
Created on Sun Jun 26 12:02:24 2022

@author: david
"""

from dotenv import load_dotenv
import os
from google.auth.transport.requests import Request

import time

import pickle
import requests
import boto3
import logging

import sys
sys.path.append('../')
from common.google_apis import create_service

# from google_apis import create_service

load_dotenv(verbose=True, override=True)

logger = logging.getLogger(__name__)

WORKING_ENV = os.getenv('WORKING_ENV', 'DEV')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')

# SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(), 'common', os.getenv('SERVICE_ACCOUNT_FILE'))  # IDE/Docker
# SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.getcwd()), 'common',
#                                     os.getenv('SERVICE_ACCOUNT_FILE'))  # Terminal
# GOOGLEDRIVE_FOLDER_ID = os.getenv('GOOGLEDRIVE_FOLDER_ID')

SCOPES = ['https://www.googleapis.com/auth/photoslibrary',
          'https://www.googleapis.com/auth/photoslibrary.sharing',
          'https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata']

API_NAME = 'photoslibrary'
API_VERSION = 'v1'
CLIENT_SECRET_FILE = 'photoslibrary_creds.json'

service = create_service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

prefix = ''
token_dir = 'token files'
pickle_file = f'token_{API_NAME}_{API_VERSION}{prefix}.pickle'
bucket = 'adoka-google-apis'

upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'

if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
    logger.info('Getting google photos token from s3')
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    logger.info(s3_client)
    s3_response_object = s3_client.get_object(Bucket=bucket, Key=token_dir + '/' + pickle_file)
    body_string = s3_response_object['Body'].read()
    cred = pickle.loads(body_string)
    if cred.expired:
        cred.refresh(Request())

    token = cred
else:
    # print(pickle_file)
    token = pickle.load(open(os.path.join(os.getcwd(), 'token files', 'token_photoslibrary_v1.pickle'), 'rb'))


# directory = os.path.join(os.getcwd(), 'giftcards')


def get_album_id(name):

    logger.info(f'Getting album id for {name}')
    albums = service.albums().list().execute()['albums']

    album = [x['id'] for x in albums if 'title' in x and x['title'] == name]

    if not album:
        request_body = {
            'album': {'title': name}
        }
        response_album = service.albums().create(body=request_body).execute()

        album_id = response_album['id']

    else:
        album_id = album[0]

    return album_id


def upload_image(image_path, upload_file_name, token=token):
    upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'

    headers = {'Authorization': 'Bearer ' + token.token, 'Content-type': 'application/octet-stream',
               'X-Goog-Upload-Protocol': 'raw', 'X-Goog-File-Name': upload_file_name,
               'X-Goog-Upload-File-Name': upload_file_name}

    img = open(image_path, 'rb').read()
    response = requests.post(upload_url, data=img, headers=headers)
    print('\nUpload token: {0}'.format(response.content.decode('utf-8')))
    logger.info('Upload token: {0}'.format(response.content.decode('utf-8')))

    return response


# Firstly must upload image using API

def batch_upload(files=None, directory=None):
    tokens = []

    if directory:
        for img in os.listdir(directory):
            image = os.path.join(directory, img)
            response = upload_image(image, img, token)
            tokens.append(response.content.decode('utf-8'))

    elif files:
        for img_path in files:
            response = upload_image(img_path, img_path.split('/')[-1], token)
            tokens.append(response.content.decode('utf-8'))

    new_media_items = [{'simpleMediaItem': {'uploadToken': tok}} for tok in tokens]

    # For single/tokens
    request_body = {
        'newMediaItems': new_media_items
    }

    service.mediaItems().batchCreate(body=request_body).execute()

    return new_media_items


# Then can move image using Api, Current can't delete items from google photos
def move_media(new_media_items, album_name='Giftcards'):
    album_id = get_album_id(album_name)

    response = service.mediaItems().list(pageSize=len(new_media_items)).execute()
    items = response.get('mediaItems')
    media_items_ids = [x['id'] for x in items]

    # For batch
    request_body = {
        'mediaItemIds': media_items_ids
    }

    # Only images added via the api can be moved/removed to album using api
    response = service.albums().batchAddMediaItems(
        albumId=album_id,
        body=request_body
    ).execute()

    return response


def get_media_items_id(album_name='Giftcards', filter_=[]):
    album_id = get_album_id(album_name)
    request_body = {'albumId': album_id, 'pageSize': 100}
    response_search = service.mediaItems().search(body=request_body).execute()
    media_items = response_search.get('mediaItems')
    nextPageToken = response_search.get('nextPageToken')
    while nextPageToken:
        request_body['pageToken'] = nextPageToken
        response_search = service.mediaItems().search(body=request_body).execute()
        media_items.extend(response_search.get('mediaItems'))
        nextPageToken = response_search.get('nextPageToken')
    return [x['id'] for x in media_items if x['filename'] in filter_] if filter_ else [x['id'] for x in media_items]


def get_media_items_name(album_name='Giftcards', filter_=[]):
    album_id = get_album_id(album_name)
    request_body = {'albumId': album_id, 'pageSize': 100}
    response_search = service.mediaItems().search(body=request_body).execute()
    media_items = response_search.get('mediaItems')
    nextPageToken = response_search.get('nextPageToken')
    while nextPageToken:
        request_body['pageToken'] = nextPageToken
        response_search = service.mediaItems().search(body=request_body).execute()
        media_items.extend(response_search.get('mediaItems'))
        nextPageToken = response_search.get('nextPageToken')

    if not media_items:
        return []
    else:
        return [x['filename'] for x in media_items if x['filename'] in filter_] if filter_ else [x['filename'] for x in
                                                                                                 media_items]


def remove_media(media_ids, album_name='Giftcards'):
    # Make note in description to delete giftcard from main photos gallery
    request_body = {
        "description": "Balance is 0. Delete this giftcard"
    }

    for id_ in media_ids:
        response = service.mediaItems().patch(id=id_, updateMask='description', body=request_body).execute()
        time.sleep(1)

    album_id = get_album_id(album_name)

    request_body = {
        'mediaItemIds': media_ids
    }

    response = service.albums().batchRemoveMediaItems(
        albumId=album_id,
        body=request_body
    ).execute()

    return response
