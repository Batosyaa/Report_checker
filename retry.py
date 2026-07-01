"""
Retry helper for transient Google API errors (429 / 5xx).
"""

import time
import functools

from googleapiclient.errors import HttpError

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def with_retry(max_attempts=3, base_delay=1):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0

            while True:
                try:
                    return func(*args, **kwargs)
                except HttpError as e:
                    status = e.resp.status if e.resp is not None else None
                    attempt += 1

                    if status not in RETRYABLE_STATUS_CODES or attempt >= max_attempts:
                        raise

                    delay = base_delay * (2 ** (attempt - 1))
                    time.sleep(delay)

        return wrapper

    return decorator
