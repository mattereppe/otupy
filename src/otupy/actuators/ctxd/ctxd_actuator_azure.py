from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient


import os, random
def main():
    subscription_id = "8f393b4c-3807-4a25-90ed-9f383b021a97"
    credential = AzureCliCredential()
    print("Hello, World")
    # Create a client for Azure Resource Manager
    client = ResourceManagementClient(credential, subscription_id)
    for rg in client.resource_groups.list():
        print(rg.name)

   

if __name__ == "__main__":
	main()