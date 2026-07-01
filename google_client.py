from google.oauth2 import service_account
from googleapiclient.discovery import build

import config



SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets"
]


def get_credentials():
    
    creds = service_account.Credentials.from_service_account_file(
        config.SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    return creds


def get_drive_service():

    creds = get_credentials()

    service = build("drive", "v3", credentials=creds)

    return service


def get_sheets_service():

    creds = get_credentials()

    service = build("sheets", "v4", credentials=creds)

    return service