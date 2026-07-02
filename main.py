"""
Оркестрация:
- получаем БИНы из Drive
- читаем Google Sheet
- обновляем таблицу
- логируем результат
"""

import sys
import time

import config
from logger import setup_logger

from drive_service import get_bin_set
from sheets_service import process_sheet


def validate_config():

    if not config.GOOGLE_DRIVE_FOLDER_ID:
        raise ValueError("GOOGLE_DRIVE_FOLDER_ID is empty. Set it in .env before running.")

    if not config.GOOGLE_SHEET_ID:
        raise ValueError("GOOGLE_SHEET_ID is empty. Set it in .env before running.")

    if not config.WORKSHEET_NAME:
        raise ValueError("WORKSHEET_NAME is empty. Set it in .env before running.")


def main():
    logger = setup_logger()

    start_time = time.time()

    logger.info("===== REPORT CHECKER STARTED =====")

    try:
        validate_config()

        logger.info("Fetching BINs from Google Drive...")
        bin_set = get_bin_set()

        logger.info(f"PDF BINs found: {len(bin_set)}")

        logger.info("Processing Google Sheet...")

        processed_rows = process_sheet(bin_set)

        logger.info(f"Rows processed: {processed_rows}")

        elapsed = round(time.time() - start_time, 2)

        logger.info("===== SUMMARY =====")
        logger.info(f"Execution time: {elapsed} sec")
        logger.info("Status: SUCCESS")

    except Exception as e:
        logger.error("===== ERROR OCCURRED =====")
        logger.error(str(e), exc_info=True)
        sys.exit(1)

    finally:
        logger.info("===== REPORT CHECKER FINISHED =====")


if __name__ == "__main__":
    main()
