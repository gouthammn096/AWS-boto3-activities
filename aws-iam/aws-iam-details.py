import os
import csv
from pytz import timezone
from datetime import date, datetime

import boto3
from botocore.exceptions import ClientError
import pandas as pd

date_format = "%Y-%m-%d"
now = datetime.now()
today = date.today()
diff_last = datetime.strptime(str(today), date_format)

dir_name = "Reports"
fields = [
    "UserName",
    "Group",
    "LastActivity",
    "KeyID",
    "LastKeyUsed",
    "ConsoleAccess",
    "MFA",
    "LastLogin",
]

# Creating Reports directory if it not exists
if not os.path.exists(dir_name):
    os.mkdir(dir_name)

try:
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
    # Iterating through each aws account
    for aws_current_account in aws_accounts.items():
        file_exists = os.path.isfile(
            dir_name + "/" + "iam_users_" + now.strftime("%d-%m-%Y %I:%M %p") + ".csv"
        )

        # boto3 resource
        iam = boto3.resource(
            "iam",
            aws_access_key_id=aws_current_account[1]["aws_aki"],
            aws_secret_access_key=aws_current_account[1]["aws_sak"],
        )

        with open(
            dir_name + "/" + "iam_users_" + now.strftime("%d-%m-%Y %I:%M %p") + ".csv", "a",
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

        for user in iam.users.all():
            user_name = []
            key_id = []
            last_key_used = []
            last_activity = []
            last_login = []
            mfa = []
            group = []
            console_access = []

            user_name.append(user.user_name)
            password_last_used = user.password_last_used

            # UserGroup listing
            group_response = iam.meta.client.list_groups_for_user(UserName=user.user_name)
            if group_response['Groups']:
                group.append(group_response['Groups'][0]['GroupName'])
            else:
                group.append("----")

            # MFA listing
            mfa_response = iam.meta.client.list_mfa_devices(UserName=user.user_name)
            if mfa_response['MFADevices'] != [] and "mfa" in mfa_response['MFADevices'][0]['SerialNumber']:
                mfa.append("Enabled")
            else:
                mfa.append("Not Enabled")

            # LastLogin
            if password_last_used is not None:
                console_access.append("Y")
                last_login_date = password_last_used.astimezone(
                    timezone("Asia/Kolkata")
                )
                last_login_date_obj = last_login_date.strftime("%d-%m-%Y, %I:%M %p")
                diff_login = last_login_date.strftime("%Y-%m-%d")
                diff_login = datetime.strptime(diff_login, date_format)
                login_days = diff_last - diff_login
                if login_days.days == 0:
                    last_login.append(last_login_date_obj + " (Today)")
                elif login_days.days == 1:
                    last_login.append(last_login_date_obj + " (Yesterday)")
                else:
                    last_login.append(last_login_date_obj + " (" + str(login_days.days) + "Days Before)"
                    )
            else:
                console_access.append("N")
                last_login.append("----")

            # Get Access Keys for the User
            keys_response = iam.meta.client.list_access_keys(UserName=user.user_name)
            last_access = None
            last_key_date = None
            if keys_response["AccessKeyMetadata"]:
                for key in keys_response["AccessKeyMetadata"]:
                    key_id.append(key["AccessKeyId"])
                    last_used_response = iam.meta.client.get_access_key_last_used(
                        AccessKeyId=key["AccessKeyId"]
                    )

                    # LastKey Used
                    if "LastUsedDate" in last_used_response["AccessKeyLastUsed"]:
                        access_key_last_used = last_used_response["AccessKeyLastUsed"]["LastUsedDate"]
                        if last_access is None or access_key_last_used < last_access:
                            last_access = access_key_last_used
                            last_key_date = last_access
                            if last_access:
                                last_access = last_access.astimezone(timezone("Asia/Kolkata"))
                                last_access_obj = last_access.strftime("%d-%m-%Y, %I:%M %p")
                                diff_first = last_access.strftime("%Y-%m-%d")
                                diff_first = datetime.strptime(diff_first, date_format)
                                access_key_days = diff_last - diff_first
                                if access_key_days.days == 0:
                                    last_key_used.append(last_access_obj + " (Today)")
                                elif access_key_days.days == 1:
                                    last_key_used.append(last_access_obj + " (Yesterday)")
                                else:
                                    last_key_used.append(
                                        last_access_obj + " (" + str(access_key_days.days) + "Days Before)"
                                    )
                        else:
                            last_key_used.append("----")
                    else:
                        last_key_used.append("----")
            else:
                key_id.append("----")
                last_key_used.append("----")

            # Last Activity
            if last_key_date and password_last_used:
                youngest_date = max(last_key_date, password_last_used)
                if youngest_date:
                    youngest_date = youngest_date.astimezone(timezone("Asia/Kolkata"))
                    youngest_date_obj = youngest_date.strftime("%d-%m-%Y, %I:%M %p")
                    diff_activity = youngest_date.strftime("%Y-%m-%d")
                    diff_activity = datetime.strptime(diff_activity, date_format)
                    activity_days = diff_last - diff_activity
                    if activity_days.days == 0:
                        last_activity.append(youngest_date_obj + " (Today)")
                    elif activity_days.days == 1:
                        last_activity.append(youngest_date_obj + " (Yesterday)")
                    else:
                        last_activity.append(
                            youngest_date_obj + " (" + str(activity_days.days) + "Days Before)"
                        )
            elif last_key_date:
                last_key_date = last_key_date.astimezone(timezone("Asia/Kolkata"))
                last_access_obj = last_access.strftime("%d-%m-%Y, %I:%M %p")
                diff_first = last_access.strftime("%Y-%m-%d")
                diff_first = datetime.strptime(diff_first, date_format)
                access_key_days = diff_last - diff_first
                if access_key_days.days == 0:
                    last_activity.append(last_access_obj + " (Today)")
                elif access_key_days.days == 1:
                    last_activity.append(last_access_obj + " (Yesterday)")
                else:
                    last_activity.append(
                        last_access_obj + " (" + str(access_key_days.days) + "Days Before)"
                    )
            elif password_last_used:
                last_login_date = password_last_used.astimezone(
                    timezone("Asia/Kolkata")
                )
                last_login_date_obj = last_login_date.strftime("%d-%m-%Y, %I:%M %p")
                diff_login = last_login_date.strftime("%Y-%m-%d")
                diff_login = datetime.strptime(diff_login, date_format)
                login_days = diff_last - diff_login
                if login_days.days == 0:
                    last_activity.append(last_login_date_obj + " (Today)")
                elif login_days.days == 1:
                    last_activity.append(last_login_date_obj + " (Yesterday)")
                else:
                    last_activity.append(last_login_date_obj + " (" + str(login_days.days) + "Days Before)"
                                      )
            else:
                last_activity.append("----")

            # Storing the data in report
            data = [user_name, group, last_activity, key_id, last_key_used, console_access, mfa, last_login]
            df = pd.DataFrame(data=data)
            transpose = df.transpose()
            transpose.to_csv(
                dir_name + "/" + "iam_users_" + now.strftime("%d-%m-%Y %I:%M %p") + ".csv",
                header=False,
                mode="a",
                index=False,
            )

except ClientError as error:
    print("An exception occurred", error)
