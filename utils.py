import boto3
import os
import sys
from botocore.exceptions import ClientError
import json
from datetime import datetime, timezone


def load_sync_state(state_file):
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {}


def save_sync_state(state_file, state):
    with open(state_file, "w") as f:
        json.dump(state, f)


def sync_s3_bucket(bucket_name, local_dir, state_file):
    s3 = boto3.client("s3")

    # Ensure local directory exists
    os.makedirs(local_dir, exist_ok=True)

    # Load previous sync state
    sync_state = load_sync_state(state_file)

    # Get bucket last modified time
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

    # Check if we need to sync
    last_sync = sync_state.get("last_sync")
    if last_sync and datetime.fromisoformat(last_sync) >= bucket_last_modified:
        print("Bucket hasn't been modified since last sync. Skipping.")
        return

    # Iterate through objects in the bucket
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            local_path = os.path.join(local_dir, key)
            etag = obj["ETag"].strip('"')

            # Check if file needs to be downloaded
            if key not in sync_state or sync_state[key]["etag"] != etag:
                print(f"Downloading {key}")
                try:
                    # Ensure the directory exists
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    # Download the file
                    s3.download_file(bucket_name, key, local_path)
                    download_success = True
                    error_message = None
                except Exception as e:
                    print(f"Error downloading {key}: {e}", file=sys.stderr)
                    download_success = False
                    error_message = str(e)

                # Update sync state regardless of download success
                sync_state[key] = {
                    "etag": etag,
                    "last_sync": obj["LastModified"].isoformat(),
                    "download_success": download_success,
                    "error_message": error_message,
                }

                # Save sync state after each file (in case of interruption)
                save_sync_state(state_file, sync_state)
            else:
                print(f"Skipping {key} - already up to date")

    # Update last sync time
    sync_state["last_sync"] = datetime.now(timezone.utc).isoformat()

    # Final save of sync state
    save_sync_state(state_file, sync_state)


if __name__ == "__main__":
    bucket_name = "st-agent-images"
    local_dir = "./data/st-agent-images-local"
    state_file = "sync_state.json"

    sync_s3_bucket(bucket_name, local_dir, state_file)
    print("Sync completed.")
