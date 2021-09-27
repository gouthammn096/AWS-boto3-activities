import os
import sys
import csv

import boto3
from botocore.exceptions import ClientError

dir_name = "Reports"
fields = ['ElasticIP']
fields1 = ['Instance Name', 'Instance Id', 'Elatic IP', 'Private IP', 'Instance State']

# Creating Reports directory if it not exists
if not os.path.exists(dir_name):
    os.mkdir(dir_name)
try:
    # Add the AWS accounts credentials below.
    aws_accounts = {

        1: {
            'aws_aka': 'First AWS Account Namethz',
            'aws_aki': '[access_key_id]',
            'aws_sak': '[secret_access_key]'
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
    regions = boto3.session.Session().get_available_regions('ec2')
    for aws_current_account in aws_accounts.items():
        if not os.path.exists(dir_name + '/' + aws_current_account[1]['aws_aka']):
            os.mkdir(dir_name + '/' + aws_current_account[1]['aws_aka'])
        for region in regions:
            try:
                ec2 = boto3.client(
                    'ec2',
                    aws_access_key_id=aws_current_account[1]['aws_aki'],
                    aws_secret_access_key=aws_current_account[1]['aws_sak'],
                    region_name=region
                )
                addresses_dict = ec2.describe_addresses()
                for eip_dict in addresses_dict['Addresses']:
                    file_exists_file1 = os.path.isfile(
                        dir_name + '/' + aws_current_account[1]['aws_aka'] + '/' + 'Allocated and not associated.csv')
                    file_exists_file2 = os.path.isfile(
                           dir_name + '/' + aws_current_account[1]['aws_aka'] + '/' + 'Allocated and associated.csv')
                    if "NetworkInterfaceId" not in eip_dict:
                        with open(dir_name + '/' + aws_current_account[1]['aws_aka'] + '/' +
                                  'Allocated and not associated.csv', 'a') as csvfile:
                            csv_writer = csv.writer(csvfile)
                            if not file_exists_file1:
                                csv_writer.writerow(fields)
                            csv_writer.writerows([[eip_dict['PublicIp']]])

                    elif "NetworkInterfaceId" in eip_dict:
                        instance_status = ec2.describe_instances(InstanceIds=[eip_dict['InstanceId']])
                        rows = []
                        with open(dir_name + '/' + aws_current_account[1]['aws_aka'] + '/' +
                                  'Allocated and associated.csv', 'a') as csvfile:
                            csv_writer = csv.writer(csvfile)
                            if not file_exists_file2:
                                csv_writer.writerow(fields1)
                            for response in instance_status['Reservations']:
                                for tag in response['Instances']:
                                    if 'Tags' not in tag:
                                        rows.append(
                                            ['NONE', eip_dict['InstanceId'],
                                             eip_dict['PublicIp'], eip_dict['PrivateIpAddress'], tag['State']['Name']])
                                        csv_writer.writerows(rows)
                                    else:
                                        for instance_name in tag['Tags']:
                                            rows.append(
                                                [instance_name['Value'], eip_dict['InstanceId'],
                                                 eip_dict['PublicIp'], eip_dict['PrivateIpAddress'], tag['State']['Name']])
                                            csv_writer.writerows(rows)

            except ClientError as e:
                print(f'The region {region} is not enabled...')

except Exception as error:
    print("An exception occurred", error)
