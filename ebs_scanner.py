import boto3
from botocore.exceptions import NoCredentialsError, NoRegionError

def find_unattached_volumes():
    try:
        ec2 = boto3.client("ec2", region_name="us-east-1")

        response = ec2.describe_volumes()

        unattached_volumes = []

        for volume in response["Volumes"]:
            if len(volume["Attachments"]) == 0:
                unattached_volumes.append(volume["VolumeId"])

        return unattached_volumes

    except NoRegionError:
        print("AWS region not configured.")

    except NoCredentialsError:
        print("AWS credentials not configured.")

    except Exception as e:
        print("Scanner failed:")
        print(e)

if __name__ == "__main__":
    volumes = find_unattached_volumes()

    if volumes is not None:
        if volumes:
            print("Unattached Volumes Found:")
            for volume in volumes:
                print(volume)
        else:
            print("No unattached volumes found.")