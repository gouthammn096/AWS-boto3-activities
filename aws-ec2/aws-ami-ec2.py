import os
import sys
import csv

import boto3


dir_name = "Reports"
path = os.getcwd()
check_ami_date = sys.argv[2]
filename = sys.argv[1] + '_output.csv'
file_exists = os.path.isfile(dir_name + '/' + filename)
fields = ['AMI_Name', 'Status', 'Date_of_creation', 'Size(GB)', 'Virtualization_type', 'root_device_type']

# Creating Reports directory if it not exists
if not os.path.exists(dir_name):
    os.mkdir(dir_name)

# ec2 object creating
ec2_client = boto3.client('ec2', region_name=sys.argv[1])
# List of images here
images = ec2_client.describe_images(Owners=['self'])
# Writing the output to a report file
with open(path + '/' + dir_name + '/' + filename, 'a') as csvfile:
    csv_writer = csv.writer(csvfile)

    if not file_exists:
        csv_writer.writerow(fields)

    rows = []
    for response in images['Images']:
        cr_date = response['CreationDate'].split('T')[0]

        if cr_date == check_ami_date:
            for volume in response['BlockDeviceMappings']:
                rows.append([response['Name'], response['State'], response['CreationDate'], volume['Ebs']['VolumeSize'],
                             response['VirtualizationType'], response['RootDeviceType']])

        # writing the data rows
    csv_writer.writerows(rows)
