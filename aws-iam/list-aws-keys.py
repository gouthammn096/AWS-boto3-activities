import boto3


try:
    # Add the AWS accounts credentials below.
    aws_accounts = {

        1: {
            'aws_aka': 'First AWS Account Name',
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

    for aws_current_account in aws_accounts.items():

        client = boto3.client(
            'iam',
            aws_access_key_id=aws_current_account[1]['aws_aki'],
            aws_secret_access_key=aws_current_account[1]['aws_sak']
        )

        # List all users here.
        users = client.list_users()

        # Creating input files here.
        with open(aws_current_account[1]['aws_aka'] + '_input.txt', 'a') as fh_input:
            fh_input.truncate(0)

            for user_key in users['Users']:

                # List access keys here.
                access_key_list = client.list_access_keys(UserName=user_key['UserName'])

                for response in access_key_list['AccessKeyMetadata']:
                    if response['Status'] == 'Active':
                        fh_input.write(response['AccessKeyId'] + "\n")

except Exception as error:
    print(error)
