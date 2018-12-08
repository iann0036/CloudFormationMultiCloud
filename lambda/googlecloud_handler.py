import traceback
import pprint

import googleapiclient.discovery
from google.oauth2 import service_account


class GoogleCloudResourceHandler:
    credentials = None

    def __init__(self, credentials):
        SCOPES = [
            'https://www.googleapis.com/auth/cloud-platform'
        ]

        self.credentials = service_account.Credentials.from_service_account_info(credentials, scopes=SCOPES)

    def process(self, event):
        if event['RequestType'] == "Create" and event['ResourceType'] == "Custom::GoogleCloud_Compute_Instance":
            return self.create_compute_instance(event['ResourceProperties'])
        else:
            raise Exception('Unhandled Google Cloud resource or request type')

    def wait_for_operation(client, project, zone, operation):
        while True:
            result = client.zoneOperations().get(
                project=project,
                zone=zone,
                operation=operation
            ).execute()

            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                return result

            time.sleep(1)

    def create_compute_instance(self, resource_properties):
        compute_client = googleapiclient.discovery.build('compute', 'v1', credentials=self.credentials)

        op = compute_client.instances().insert(
            project=resource_properties['Project'],
            zone=resource_properties['Zone'],
            body={
                'name': resource_properties['Name'],
                'machineType': "zones/%s/machineTypes/%s" % (resource_properties['Zone'], resource_properties['MachineType']),

                # Specify the boot disk and the image to use as a source.
                'disks': [
                    {
                        'boot': True,
                        'autoDelete': True,
                        'initializeParams': {
                            'sourceImage': 'https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/family/debian-9',
                        }
                    }
                ],

                # Specify a network interface with NAT to access the public
                # internet.
                'networkInterfaces': [{
                    'network': 'global/networks/default',
                    'accessConfigs': [
                        {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                    ]
                }],

                # Allow the instance to access cloud storage and logging.
                'serviceAccounts': [{
                    'email': 'default',
                    'scopes': [
                        'https://www.googleapis.com/auth/devstorage.read_write',
                        'https://www.googleapis.com/auth/logging.write'
                    ]
                }]
            }
        ).execute()

        self.wait_for_operation(compute_client, resource_properties['Project'], resource_properties['Zone'], op['name'])
        
        return response
