import boto3

def test_auth():
    try:
        session = boto3.Session()
        sts = session.client("sts")
        identity = sts.get_caller_identity()

        print("Authentication Successful")
        print("Account:", identity["Account"])

    except Exception as e:
        print("Authentication Failed")
        print(e)

if __name__ == "__main__":
    test_auth()
