import boto3
import time
import streamlit as st
import configparser
credents = configparser.ConfigParser()
credents.read_file(open('credential.conf'))

#Reading in the credentials into Python variables. No can see them
aws_key = credents["AWS"]["KEY"]
aws_secret = credents["AWS"]["SECRET"]
region = credents["AWS"]["REGION"]

class textractProcessor:
    def __init__(self, bucketName, docName):
        self.bucketName = bucketName
        self.docName = docName

    def processDocument(self):
        region = "us-east-1"
        client = boto3.client(service_name = 'textract', aws_access_key_id=aws_key,aws_secret_access_key=aws_secret, region_name=region)
        job_id = start_job(client, self.bucketName, self.docName)
        print("Started job with id: {}".format(job_id))
        if is_job_complete(client, job_id):
            response = get_job_results(client, job_id)
        # print(response)

        formattedResponse = ''
        # Print detected text
        for result_page in response:
            for item in result_page["Blocks"]:
                if item["BlockType"] == "LINE":
                    formattedResponse += item["Text"] + ', '
                    print('\033[94m' + item["Text"] + '\033[0m')

        # Remove the trailing comma and space
        if formattedResponse.endswith(', '):
            formattedResponse = formattedResponse[:-2]
        print(formattedResponse)
        return formattedResponse

def start_job(client, s3_bucket_name, object_name):
    response = None
    response = client.start_document_text_detection(
        DocumentLocation={
            'S3Object': {
                'Bucket': s3_bucket_name,
                'Name': object_name
            }})
    return response["JobId"]

def is_job_complete(client, job_id):
    time.sleep(1)
    response = client.get_document_text_detection(JobId=job_id)
    status = response["JobStatus"]
    print("Job status: {}".format(status))

    with st.spinner('Processing uploade file...'):
        while(status == "IN_PROGRESS"):
            time.sleep(1)
            response = client.get_document_text_detection(JobId=job_id)
            status = response["JobStatus"]
            print("Job status: {}".format(status))
    st.write("File process successfully!")
    return status

def get_job_results(client, job_id):
    pages = []
    time.sleep(1)
    response = client.get_document_text_detection(JobId=job_id)
    pages.append(response)
    print("Resultset page received: {}".format(len(pages)))
    next_token = None
    if 'NextToken' in response:
        next_token = response['NextToken']

    while next_token:
        time.sleep(1)
        response = client.\
            get_document_text_detection(JobId=job_id, NextToken=next_token)
        pages.append(response)
        print("Resultset page received: {}".format(len(pages)))
        next_token = None
        if 'NextToken' in response:
            next_token = response['NextToken']

    return pages