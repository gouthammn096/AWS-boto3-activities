import os
import csv
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

date = datetime.today().strftime("%d-%m-%Y")
dir_name = "Reports"
fields = [
    "SI No",
    "Instance Name",
    "Instance Id",
    "Elastic IP",
    "Private IP",
    "Instance State",
]
fields_unassociated = ["SI No", "Elastic IP"]

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
    regions = boto3.session.Session().get_available_regions("ec2")
    for aws_current_account in aws_accounts.items():
        if not os.path.exists(dir_name + "/" + aws_current_account[1]["aws_aka"]):
            os.mkdir(dir_name + "/" + aws_current_account[1]["aws_aka"])
        previous_region = []
        previous_region_eip = []

        with open(
            dir_name
            + "/"
            + aws_current_account[1]["aws_aka"]
            + "/"
            + "Allocated and associated.csv",
            "a",
        ) as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerows(
                [["Account Alias", aws_current_account[1]["aws_aka"]], ["Date", date]]
            )
            for region in regions:
                unassociated_ips = []
                serial_number = 1
                serial_number_1 = 1
                previous_instance_id = []
                try:
                    ec2 = boto3.resource(
                        "ec2",
                        aws_access_key_id=aws_current_account[1]["aws_aki"],
                        aws_secret_access_key=aws_current_account[1]["aws_sak"],
                        region_name=region,
                    )

                    for elastic_ip in ec2.vpc_addresses.all():
                        if (
                            len(previous_region_eip) == 0
                            or region != previous_region_eip[-1]
                        ):
                            csv_writer.writerow([])
                            csv_writer.writerow(["Region Name", region])
                            csv_writer.writerow([])
                            csv_writer.writerow(fields)
                            previous_region_eip.append(region)
                        if (
                            len(previous_instance_id) != 0
                            and elastic_ip.instance_id is not None
                            and elastic_ip.instance_id != previous_instance_id[-1]
                        ):
                            serial_number += 1
                        if elastic_ip.network_interface_id:
                            rows = []
                            instance_name = ""
                            instance = ec2.Instance(elastic_ip.instance_id)
                            for tag_name in instance.tags:
                                if tag_name["Key"] == "Name":
                                    instance_name += tag_name["Value"]
                            rows.append(
                                [
                                    serial_number,
                                    instance_name,
                                    elastic_ip.instance_id,
                                    elastic_ip.public_ip,
                                    elastic_ip.private_ip_address,
                                    instance.state["Name"],
                                ]
                            )
                            previous_instance_id.append(elastic_ip.instance_id)
                            csv_writer.writerows(rows)
                        else:
                            unassociated_ips.append(elastic_ip)
                    for unassociated_ip in unassociated_ips:
                        rows = []
                        if len(previous_region) == 0 or region != previous_region[-1]:
                            csv_writer.writerow(["Unassociated Elastic IPs"])
                            csv_writer.writerow(fields_unassociated)
                            previous_region.append(region)
                        rows.append([serial_number_1, unassociated_ip.public_ip])
                        csv_writer.writerows(rows)
                        serial_number_1 += 1
                except ClientError:
                    print(f"The region {region} is not enabled...")

except Exception as error:
    print("An exception occurred", error)
