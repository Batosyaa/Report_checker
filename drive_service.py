"""
Drive Service

Отвечает за:
- получение файлов из папки
- извлечение БИНов из PDF имен
"""

from pathlib import Path

from google_client import get_drive_service
from retry import with_retry
import config


@with_retry()
def _list_files_page(service, query, page_token):
    return service.files().list(
        q=query,
        fields="nextPageToken, files(id, name)",
        pageToken=page_token
    ).execute()


def get_pdf_files():

    service = get_drive_service()

    query = f"'{config.GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false"

    files = []
    page_token = None

    while True:
        results = _list_files_page(service, query, page_token)

        files.extend(results.get("files", []))

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return files


def extract_bins_from_files(files):

    valid_extensions = {ext.lower() for ext in config.VALID_EXTENSIONS}

    bin_set = set()

    for f in files:
        name = f["name"]
        path = Path(name)

        if path.suffix.lower() in valid_extensions:
            bin_value = path.stem.strip()
            bin_set.add(bin_value)

    return bin_set


def get_bin_set():

    files = get_pdf_files()
    return extract_bins_from_files(files)
