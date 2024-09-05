import boto3
import os
import sys
from botocore.exceptions import ClientError
import json
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def load_sync_state(state_file):
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {}


def save_sync_state(state_file, state):
    with open(state_file, "w") as f:
        json.dump(state, f)


def download_file(s3, bucket_name, key, local_path):
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        s3.download_file(bucket_name, key, local_path)
        return True, None
    except Exception as e:
        return False, str(e)


def sync_s3_bucket(bucket_name, local_dir, state_file, max_workers=10, retry_limit=3):
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
    except Exception as e:
        print(f"Error accessing bucket: {e}", file=sys.stderr)
        return

    last_sync = sync_state.get("last_sync")
    if last_sync and datetime.fromisoformat(last_sync) >= bucket_last_modified:
        print("Bucket hasn't been modified since last sync. Skipping.")
        return

    paginator = s3.get_paginator("list_objects_v2")
    files_to_download = []

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            local_path = os.path.join(local_dir, key)
            etag = obj["ETag"].strip('"')

            if key not in sync_state or sync_state[key]["etag"] != etag:
                files_to_download.append((key, local_path, etag, obj["LastModified"]))

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
                return True
            retries += 1
            time.sleep(2**retries)  # Exponential backoff for retries
        return False

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_file, file): file for file in files_to_download
        }
        for future in as_completed(futures):
            file = futures[future]
            if not future.result():
                print(
                    f"Failed to download {file[0]} after multiple retries.",
                    file=sys.stderr,
                )

    sync_state["last_sync"] = datetime.now(timezone.utc).isoformat()
    save_sync_state(state_file, sync_state)
    print("Sync completed.")


if __name__ == "__main__":
    bucket_name = "st-agent-images"
    local_dir = "./data/st-agent-images-local"
    state_file = "sync_state.json"
    sync_s3_bucket(bucket_name, local_dir, state_file)
