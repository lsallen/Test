# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import os
import asyncio
import sys
import signal
import threading
from azure.iot.device.aio import IoTHubModuleClient
#from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from datetime import datetime
# Event indicating client stop
stop_event = threading.Event()


def create_client():
    client = IoTHubModuleClient.create_from_edge_environment()

    return client


async def run_sample(client):
    #connection string for the local
    STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=http;BlobEndpoint=http://10.209.9.47:11002/gatewaystorage;AccountName=gatewaystorage;AccountKey=aARk5M12K0xCSo7G5yCNSA==;"
    STORAGE_CONTAINER_NAME = "localblob"
    STORAGE_LOCAL_PATH = "./UploadBlob"

    os.makedirs(STORAGE_LOCAL_PATH, exist_ok=True)
    print(os.getcwd())
#instantiate a containerclient to interact with local container, although this container may not yet exist
    container_client = ContainerClient.from_connection_string(
        conn_str=STORAGE_CONNECTION_STRING, container_name=STORAGE_CONTAINER_NAME)
    try:
        #get the properties of the container (if it already exists or not and etc...)
        container_properties = container_client.get_container_properties()
        print(container_properties)
        #if this container doesn't exist, then create it
    except Exception as e:
        container_client.create_container()
        print(e)      
    while True:
        try:
            local_filename = "Hi" + str(datetime.now()) + ".txt"
            upload_file_path = os.path.join(STORAGE_LOCAL_PATH, local_filename)
            
            with open(upload_file_path, "w") as my_file:
                my_file.write("hello: " + str(datetime.now()))
#create a blob client to interact with specific blob, although blob may not yet exist
            blob = BlobClient.from_connection_string(
                conn_str=STORAGE_CONNECTION_STRING, container_name=STORAGE_CONTAINER_NAME, blob_name=local_filename)
            with open(upload_file_path, "rb") as data:
                blob.upload_blob(data)
                print('Upload Success!')
        except Exception as e:
            print('Upload Failed...')
            print(e)
        asyncio.sleep(3)


def main():
    if not sys.version >= "3.5.3":
        raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
    print ( "IoT Hub Client for Python" )

    # NOTE: Client is implicitly connected due to the handler being set on it
    client = create_client()

    # Define a handler to cleanup when module is is terminated by Edge
    def module_termination_handler(signal, frame):
        print ("IoTHubClient sample stopped by Edge")
        stop_event.set()

    # Set the Edge termination handler
    signal.signal(signal.SIGTERM, module_termination_handler)

    # Run the sample
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_sample(client))
    except Exception as e:
        print("Unexpected error %s " % e)
        raise
    finally:
        print("Shutting down IoT Hub Client...")
        loop.run_until_complete(client.shutdown())
        loop.close()


if __name__ == "__main__":
    main()
