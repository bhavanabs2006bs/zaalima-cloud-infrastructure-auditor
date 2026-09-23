import boto3
import time

MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    try:
        sts = boto3.client("sts")
        response = sts.get_caller_identity()

        print("Success")
        print(response["Account"])
        break

    except Exception as e:
        print(f"Attempt {attempt + 1} failed")

        if attempt < MAX_RETRIES - 1:
            time.sleep(2)
        else:
            print("Maximum retries reached")
            print(e)