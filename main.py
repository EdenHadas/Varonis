"""
PIP:
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install pyminizip (C++ required
)
"""

from __future__ import print_function

import os
import io
import pyminizip
import hashlib
from zipfile import ZipFile

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

FILE_NAME = 'readme.txt'
ZIP_NAME = 'myzipfile.zip'
FILE_TYPE = 'application/zip'
PASSWORD = 'pass123'
EXTRACTION_PATH = './extraction_folder'
HASH_ZIP_NAME = 'hash_zipfile.zip'


def connect_to_drive_api():
    """
    Shows basic usage of the Drive v3 API.
    Create Credentials to Goggle App
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        return creds
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())


GOOGLE_APPLICATION_CREDENTIALS = connect_to_drive_api()


def create_pass_zip_file():

    with open(FILE_NAME, 'w') as myfile:
        myfile.write('some random text')
    pyminizip.compress(FILE_NAME, None, ZIP_NAME, PASSWORD, 0)
    print("Created protected zip file")


def create_zip_file(hash_value):
    with ZipFile(HASH_ZIP_NAME, 'w') as myzip:
        with myzip.open("my_hash_file.txt", 'w') as myfile:
            myfile.write(hash_value.encode())
    print("Created hash zip file")


def upload_file(zip_name):
    """Upload new file to Google Drive
    Returns : Id's of the file uploaded
    """
    creds = GOOGLE_APPLICATION_CREDENTIALS

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {'name': zip_name, 'mimetype': FILE_TYPE}
        media = MediaFileUpload(zip_name, mimetype=FILE_TYPE)
        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, media_body=media,
                                      fields='id').execute()
        print(F'File ID: {file.get("id")}')

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    return file.get('id')


def download_file(file_id):
    """Downloads a file
    Args:
        real_file_id: ID of the file to download
    Returns : IO object with location.

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    creds = GOOGLE_APPLICATION_CREDENTIALS

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)

        # pylint: disable=maybe-no-member
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(F'Download {int(status.progress() * 100)}.')

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    return file.getvalue()


def extract_zip_file():
    """
    Extract the passord protected file we downloaded from Google Drive
    Creting a new fol
    :return:
    """
    if not os.path.exists(EXTRACTION_PATH):
        os.mkdir(EXTRACTION_PATH)       #creating extraction folder
    with ZipFile(ZIP_NAME) as zf:
        zf.extractall(path=EXTRACTION_PATH ,pwd=PASSWORD.encode())
    print("Extracted files from zip file")


def calc_hash_value():
    """
    Calculate hash value of the file we extracted from the zip file we downloaded from google drive
    :return: hash value
    """
    h = hashlib.sha1()
    with open(EXTRACTION_PATH + './' + FILE_NAME, 'rb') as file:
        chunk = 0
        while chunk != b'':
            # read only 1024 bytes at a time
            chunk = file.read(1024)
            h.update(chunk)
    return h.hexdigest()


def main():
    create_pass_zip_file()
    file_id = upload_file(ZIP_NAME)
    print(download_file(file_id))
    extract_zip_file()
    hash_value = calc_hash_value()
    print("The hash value id: " + hash_value)
    create_zip_file(hash_value)
    hash_file_id = upload_file(HASH_ZIP_NAME)


if __name__ == '__main__':
    main()