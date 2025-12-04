import logging
import boto3
from botocore.exceptions import ClientError
import os

# --- Load Credentials from credentials.env ---
def load_credentials():
    env_file = "credentials.env"
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_credentials()
# ---------------------------------------------

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

if __name__ == "__main__":
    # Example usage
    # Ensure you have your AWS credentials set up in ~/.aws/credentials
    # or export AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.
    
    FILE_NAME = "alertSound.wav"  # Replace with your file path
    BUCKET_NAME = "har-test-ebi" # Replace with your bucket name
    
    # Create a dummy file for testing if it doesn't exist
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, "w") as f:
            f.write("This is a test file for S3 upload.")
            
    print(f"Uploading {FILE_NAME} to {BUCKET_NAME}...")
    
    # Note: This will fail if credentials or bucket are invalid
    # success = upload_file(FILE_NAME, BUCKET_NAME)
    # if success:
    #     print("Upload Successful")
    # else:
    #     print("Upload Failed")
    
    print("Script ready. Please configure BUCKET_NAME and ensure AWS credentials are set.")
