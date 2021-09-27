import os
import csv
from pytz import timezone
from datetime import date, datetime

import boto3
import logging
from botocore.exceptions import ClientError
import pandas as pd

now = datetime.now()
dir_name = "Reports"
fields = ["Bucket Name", "Access", "Region", "Created Date"]
# Creating Reports directory if it not exists
if not os.path.exists(dir_name):
    os.mkdir(dir_name)
public_acl_indicator = "http://acs.amazonaws.com/groups/global/AllUsers"
public_buckets = {}

# Add the AWS accounts credentials below.
aws_accounts = {
    1: {
        "aws_aka": "First AWS Account Name",
        "aws_aki": "[access_key_id]",
        "aws_sak": "[secret_access_key]",
    },
    2: {
        'aws_aka': 'Second AWS Account Name',
        'aws_aki': '[access_key_id]',
        'aws_sak': '[secret_access_key]'
    },
    
    3: {
        'aws_aka': 'Third AWS Account Name',
        'aws_aki': '[access_key_id]',
        'aws_sak': '[secret_access_key]'
        }
}

for aws_current_account in aws_accounts.items():
    # boto3 session login
    session = boto3.Session(
        aws_access_key_id=aws_current_account[1]["aws_aki"],
        aws_secret_access_key=aws_current_account[1]["aws_sak"],
    )
    s3_client = session.client("s3",)
    buckets = s3_client.list_buckets()
    s3_control = session.client("s3control")
    account_id = session.client("sts").get_caller_identity().get("Account")
    account_public_access = s3_control.get_public_access_block(AccountId=account_id)
    
    with open(
        dir_name + "/" + aws_current_account[1]["aws_aka"] + "_s3_buckets.csv", "a",
    ) as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([])
        csv_writer.writerows(
            [
                ["Account Alias", aws_current_account[1]["aws_aka"]],
                ["Date & Time Of Execution", now.strftime("%d-%m-%Y %I:%M %p")],
            ]
        )
        csv_writer.writerow([])
        csv_writer.writerow(fields)

    for bucket in buckets["Buckets"]:
        BUCK_POLICY = False
        ACL_POLICY = False
        bucket_name = []
        access_type = []
        region = []
        created_date = []
        utc_time = bucket["CreationDate"]
        ist_time = utc_time.astimezone(timezone("Asia/Kolkata"))
        bucket_name.append(bucket["Name"])
        created_date.append(ist_time.strftime("%d-%m-%Y %I:%M %p"))
        location = s3_client.get_bucket_location(Bucket=bucket["Name"])[
            "LocationConstraint"
        ]
        region.append(location)
        bucket_public_access = s3_client.get_public_access_block(Bucket=bucket["Name"])
        acl_policy = s3_client.get_bucket_acl(Bucket=bucket["Name"])

        if (
            account_public_access["PublicAccessBlockConfiguration"]["BlockPublicPolicy"]
            and account_public_access["PublicAccessBlockConfiguration"][
                "BlockPublicAcls"
            ]
        ) or (
            bucket_public_access["PublicAccessBlockConfiguration"]["BlockPublicPolicy"]
            and bucket_public_access["PublicAccessBlockConfiguration"][
                "BlockPublicAcls"
            ]
        ):
            access_type.append("Bucket and objects not public")
        elif acl_policy["Grants"]:
            for grant in acl_policy["Grants"]:
                if (
                    grant["Grantee"]["Type"] == "Group"
                    and grant["Grantee"]["URI"] == public_acl_indicator
                ):
                    ACL_POLICY = True

        try:
            buck_policy = s3_client.get_bucket_policy_status(Bucket=bucket["Name"])
            if buck_policy["PolicyStatus"]["IsPublic"]:
                BUCK_POLICY = True

        except ClientError as e:
            logging.error(e.response["Error"]["Code"])

        if BUCK_POLICY and ACL_POLICY:
            access_type.append("Public (Bucket Policy and ACL)")
        elif BUCK_POLICY:
            access_type.append("Public (Bucket Policy)")
        elif ACL_POLICY:
            access_type.append("Public (ACL)")
        if not access_type:
            access_type.append("Objects can be public")

        data = [bucket_name, access_type, region, created_date]
        df = pd.DataFrame(data=data)
        transpose = df.transpose()
        transpose.to_csv(
            dir_name + "/" + aws_current_account[1]["aws_aka"] + "_s3_buckets.csv",
            header=False,
            mode="a",
            index=False,
        )
