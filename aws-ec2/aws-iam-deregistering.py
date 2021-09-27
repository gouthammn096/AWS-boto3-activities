# This script will search for all instances having a tag named "Backup" with a value of "Backup".
# As soon as we have the instances list, we loop through each instance
# and reference the AMIs of that instance. We check that the latest daily backup
# succeeded then we store every image that's reached its DeleteOn tag's date for
# deletion. We then loop through the AMIs, deregister them and remove all the
# snapshots associated with that AMI.

import datetime
import time
import boto3

ec = boto3.client("ec2", "us-west-1")
ec2 = boto3.resource("ec2", "us-west-1")
images = ec2.images.filter(Owners=["self"])


def lambda_handler():

    reservations = ec.describe_instances(
        Filters=[{"Name": "tag-key", "Values": ["backup", "Backup"]},]
    ).get("Reservations", [])

    instances = sum([[i for i in r["Instances"]] for r in reservations], [])

    print("Found %d instances that need evaluated" % len(instances))

    date = datetime.datetime.now()
    date_fmt = date.strftime("%d-%m-%Y")

    imagesList = []
    backupSuccess = False

    # Loop through all of our instances with a tag named "Backup"
    for instance in instances:
        imagecount = 0

        # Loop through each image of our current instance
        for image in images:

            if image.name.startswith("Lambda - " + instance["InstanceId"]):

                # Count this image's occcurance
                imagecount = imagecount + 1

                try:
                    if image.tags is not None:
                        deletion_date = [
                            t.get("Value") for t in image.tags if t["Key"] == "DeleteOn"
                        ][0]
                        delete_date = time.strptime(deletion_date, "%d-%m-%Y")
                except IndexError:
                    delete_date = False

                today_time = datetime.datetime.now().strftime("%m-%d-%Y")
                today_date = time.strptime(today_time, "%m-%d-%Y")

                # If image's DeleteOn date is less than or equal to today,
                # add this image to our list of images to process later
                if delete_date <= today_date:
                    imagesList.append(image.id)

                if image.name.endswith(date_fmt):
                    # Our latest backup from our other Lambda Function succeeded
                    backupSuccess = True
                    print("Latest backup from " + date_fmt + " was a success")
        print(
            "instance " + instance["InstanceId"] + " has " + str(imagecount) + " AMIs"
        )

    print("=============")

    print("About to process the following AMIs:")
    print(imagesList)
    if backupSuccess == True:

        myAccount = boto3.client("sts").get_caller_identity()["Account"]
        snapshots = ec.describe_snapshots(MaxResults=1000, OwnerIds=[myAccount])[
            "Snapshots"
        ]

        # loop through list of image IDs
        for image in imagesList:
            print("deregistering image %s" % image)
            amiResponse = ec.deregister_image(DryRun=False, ImageId=image,)

            for snapshot in snapshots:
                if snapshot["Description"].find(image) > 0:
                    snap = ec.delete_snapshot(SnapshotId=snapshot["SnapshotId"])
                    print("Deleting snapshot " + snapshot["SnapshotId"])
                    print("-------------")
    else:
        print("No current backup found. Termination suspended.")
lambda_handler()