import boto3
import os
import sys
from botocore.exceptions import ClientError
from datetime import datetime, timezone


def get_local_file_info(local_dir):
    local_files = {}
    for root, _, files in os.walk(local_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, local_dir)
            local_files[rel_path] = os.path.getmtime(full_path)
    return local_files


def sync_s3_bucket(bucket_name, local_dir):
    s3 = boto3.client("s3")

    # Ensure local directory exists
    os.makedirs(local_dir, exist_ok=True)

    # Get info about local files
    local_files = get_local_file_info(local_dir)

    # Iterate through objects in the bucket
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            local_path = os.path.join(local_dir, key)

            # Check if file needs to be downloaded
            if (
                key not in local_files
                or obj["LastModified"].replace(tzinfo=timezone.utc).timestamp()
                > local_files[key]
            ):
                print(f"Downloading {key}")
                try:
                    # Ensure the directory exists
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    # Download the file
                    s3.download_file(bucket_name, key, local_path)
                except ClientError as e:
                    print(f"Error downloading {key}: {e}", file=sys.stderr)
            else:
                print(f"Skipping {key} - already up to date")


if __name__ == "__main__":
    bucket_name = "st-agent-images"
    local_dir = "./data/st-agent-images-local"

    sync_s3_bucket(bucket_name, local_dir)
    print("Sync completed.")
