"""
Drive Service

Отвечает за:
- получение файлов из папки
- извлечение БИНов из PDF имен
"""

from google_client import get_drive_service
import config


def get_pdf_files():

    service = get_drive_service()

    query = f"'{config.GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false"

    results = service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()

    files = results.get("files", [])

    return files


def extract_bins_from_files(files):

    bin_set = set()

    for f in files:
        name = f["name"]

        if name.endswith(".pdf"):
            bin_value = name.replace(".pdf", "").strip()
            bin_set.add(bin_value)

    return bin_set


def get_bin_set():

    files = get_pdf_files()
    return extract_bins_from_files(files)