import boto3
import os
import sys
import logging
from botocore.exceptions import ClientError
import json
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for verbose output
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def load_sync_state(state_file):
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            logging.debug(f"Loading sync state from {state_file}")
            return json.load(f)
    logging.debug(f"No sync state found at {state_file}, starting fresh.")
    return {}


def save_sync_state(state_file, state):
    with open(state_file, "w") as f:
        logging.debug(f"Saving sync state to {state_file}")
        json.dump(state, f)


def download_file(s3, bucket_name, key, local_path):
    try:
        logging.debug(f"Creating directories for {local_path} if they don't exist.")
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        logging.info(f"Downloading {key} to {local_path}")
        s3.download_file(bucket_name, key, local_path)
        logging.debug(f"Download of {key} completed successfully.")
        return True, None
    except Exception as e:
        logging.error(f"Error downloading {key}: {e}")
        return False, str(e)


def sync_s3_bucket(
    bucket_name, local_dir, state_file, subfolder=None, max_workers=10, retry_limit=3
):
    s3 = boto3.client("s3")
    os.makedirs(local_dir, exist_ok=True)
    sync_state = load_sync_state(state_file)

    try:
        bucket_info = s3.head_bucket(Bucket=bucket_name)
        bucket_last_modified = bucket_info["ResponseMetadata"]["HTTPHeaders"].get(
            "last-modified"
        )
        if bucket_last_modified:
            bucket_last_modified = datetime.strptime(
                bucket_last_modified, "%a, %d %b %Y %H:%M:%S %Z"
            ).replace(tzinfo=timezone.utc)
        else:
            bucket_last_modified = datetime.now(timezone.utc)
        logging.info(f"Bucket {bucket_name} last modified at {bucket_last_modified}")
    except Exception as e:
        logging.error(f"Error accessing bucket {bucket_name}: {e}")
        return

    last_sync = sync_state.get("last_sync")
    if last_sync and datetime.fromisoformat(last_sync) >= bucket_last_modified:
        logging.info("Bucket hasn't been modified since last sync. Skipping.")
        return

    paginator = s3.get_paginator("list_objects_v2")
    prefix = subfolder if subfolder else ""
    logging.info(f"Starting sync for bucket {bucket_name}, subfolder {prefix}")

    files_to_download = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        logging.debug(f"Processing page of results for prefix {prefix}")
        for obj in page.get("Contents", []):
            key = obj["Key"]
            local_path = os.path.join(local_dir, os.path.relpath(key, prefix))
            etag = obj["ETag"].strip('"')

            if key not in sync_state or sync_state[key]["etag"] != etag:
                logging.info(f"File {key} needs to be downloaded.")
                files_to_download.append((key, local_path, etag, obj["LastModified"]))
            else:
                logging.debug(f"File {key} is already up to date.")

    if not files_to_download:
        logging.info("All files are up to date, nothing to download.")
    else:
        logging.info(f"Found {len(files_to_download)} files to download.")

    def process_file(file):
        key, local_path, etag, last_modified = file
        retries = 0
        while retries < retry_limit:
            download_success, error_message = download_file(
                s3, bucket_name, key, local_path
            )
            if download_success:
                sync_state[key] = {
                    "etag": etag,
                    "last_sync": last_modified.isoformat(),
                    "download_success": download_success,
                    "error_message": error_message,
                }
                logging.debug(f"Updated sync state for {key}")
                return True
            retries += 1
            logging.warning(f"Retry {retries} for {key} after error: {error_message}")
            time.sleep(2**retries)  # Exponential backoff for retries
        logging.error(f"Failed to download {key} after {retry_limit} retries.")
        return False

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_file, file): file for file in files_to_download
        }
        for future in as_completed(futures):
            file = futures[future]
            if not future.result():
                logging.error(f"Failed to download {file[0]} after multiple retries.")

    sync_state["last_sync"] = datetime.now(timezone.utc).isoformat()
    save_sync_state(state_file, sync_state)
    logging.info("Sync completed.")


if __name__ == "__main__":
    bucket_name = "st-public-assets"
    local_dir = "data/st-agent-images-local"
    state_file = "sync_state.json"
    subfolder = "images/agents/"  # Set your desired subfolder here
    sync_s3_bucket(bucket_name, local_dir, state_file, subfolder=subfolder)
