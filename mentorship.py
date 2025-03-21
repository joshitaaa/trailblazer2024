import streamlit as st
import boto3
import time
import json
import pandas as pd 

from queryKB import queryCourse, querySkill
from queryLLM import LLM

import configparser
credents = configparser.ConfigParser()
credents.read_file(open('credential.conf'))

#Reading in the credentials into Python variables. No can see them
aws_key = credents["AWS"]["KEY"]
aws_secret = credents["AWS"]["SECRET"]
region = credents["AWS"]["REGION"]

# Knowledge base id
kb_id = "RX7P9LOSZ5"

# Initialize Textract client
textract_client = boto3.client('textract', aws_access_key_id=aws_key,
                            aws_secret_access_key=aws_secret, region_name=region)

# Initialize S3 client
s3_client = boto3.client('s3', aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region)
bucket_name = 'unchanged-cvs'
extracted_data_bucket = 'extracted-cvs-data'
occupations_bucket = 'occupation-titles'

# Initialize session state attributes if they do not exist
if "exp" not in st.session_state:
    st.session_state.exp = ''

if "job" not in st.session_state:
    st.session_state.job = ''

if "cv" not in st.session_state:
    st.session_state.cv = ''

# Function to load occupation titles from S3
def load_occupations_from_s3(bucket_name, key):
    s3_client = boto3.client('s3', aws_access_key_id=aws_key, aws_secret_access_key=aws_secret, region_name=region)
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    content = response['Body'].read().decode('utf-8')
    occupations = json.loads(content)
    return occupations

# Load occupations from S3
occupations = load_occupations_from_s3(occupations_bucket, 'occupations.json')

# Function to upload a file to S3 with a key
def upload_file_to_s3(file, key):
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=file)

# Function to upload extracted data file to S3 with a key
def upload_extracted_data_to_s3(data, key):
    s3_client.put_object(Bucket=extracted_data_bucket, Key=key, Body=json.dumps(data).encode('utf-8'))

# Function to start PDF analysis
def start_pdf_analysis(bucket, document):
    response = textract_client.start_document_analysis(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': document}},
        FeatureTypes=['TABLES', 'FORMS']
    )
    return response['JobId']

# Function to get job status
def get_job_status(job_id):
    response = textract_client.get_document_analysis(JobId=job_id)
    status = response['JobStatus']
    return status, response

# Function to wait for job completion
def wait_for_job_completion(job_id):
    while True:
        status, response = get_job_status(job_id)
        if status in ['SUCCEEDED', 'FAILED']:
            return response
        time.sleep(5)

# Function to extract skills from PDF
def extract_skills_from_pdf(bucket, document):
    job_id = start_pdf_analysis(bucket, document)
    response = wait_for_job_completion(job_id)
    return response

# Function to process Textract response
def process_textract_response(response):
    extracted_data = {}
    blocks = response.get("Blocks", [])
    
    # Create a dictionary to hold the block relationships
    id_to_block_map = {block["Id"]: block for block in blocks}

    def get_text(block_id):
        text = ""
        block = id_to_block_map.get(block_id)
        if block and "Relationships" in block:
            for relationship in block["Relationships"]:
                if relationship["Type"] == "CHILD":
                    for child_id in relationship["Ids"]:
                        child_block = id_to_block_map.get(child_id)
                        if child_block and "Text" in child_block:
                            text += child_block["Text"] + " "
        return text.strip()

    for block in blocks:
        if block["BlockType"] == "KEY_VALUE_SET" and "EntityTypes" in block and "KEY" in block["EntityTypes"]:
            key = get_text(block["Id"])
            value = ""
            
            for relationship in block.get("Relationships", []):
                if relationship["Type"] == "VALUE":
                    for value_id in relationship["Ids"]:
                        value_block = id_to_block_map.get(value_id)
                        value += get_text(value_id)

            key = key.strip()
            value = value.strip()
            extracted_data[key] = value

    return extracted_data

experience_levels = ["Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"]

# Function to display the form
def intro_form(occupations):
    with st.form("Employee Details"):
        user_name = st.text_input("Name")
        user_occupations = st.multiselect("Select your desired occupations:", occupations)
        user_experience_level = st.selectbox("Select your experience level:", experience_levels)
        user_cv = st.file_uploader("Upload your CV below", type=["pdf", "docx"])
        submitted = st.form_submit_button("Submit")
    with st.spinner("File is uploading and analyzing..."):
        if submitted and user_name and user_cv:
            st.session_state.exp = user_experience_level
            st.session_state.job = ", ".join(user_occupations)

            # Upload CV to S3
            file_key = user_name.replace(' ', '_') + ".pdf"
            upload_file_to_s3(user_cv, file_key)
            
            # Analyze CV using Textract
            response = extract_skills_from_pdf(bucket_name, file_key)
            st.session_state.show_form = False
            st.write("File uploaded and analyzed successfully!")

            # Process and store extracted data
            extracted_data = process_textract_response(response)
            extracted_data['desired_occupations'] = user_occupations
            extracted_data['experience_level'] = user_experience_level
            extracted_data['cv_reference'] = f"s3://{bucket_name}/{file_key}"
            st.session_state.cv = json.dumps(extracted_data)
            print("extract cv: " + st.session_state.cv)

            # Upload extracted data to S3
            extracted_data_key = user_name.replace(' ', '_') + "_extracted.json"
            upload_extracted_data_to_s3(extracted_data, extracted_data_key)

st.set_page_config(page_title="Mentorship")
st.title("Training Recommendations for Employees :books:")
st.subheader("Get course recommendations based on your CV and aspirations!")

# Keeps track of chat history if we want to save somewhere
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# To only show form upon clicking the button
if "show_form" not in st.session_state:
    st.session_state.show_form = False

for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

prompt = st.chat_input("Say something")

# Starting Message
with st.chat_message("assistant"):
    start_button = st.button("Get Training Recommendations", key="training-rec")
    if start_button:
        st.session_state.show_form = True

# Control display of the intro form
if st.session_state.show_form:
    with st.chat_message("assistant"):
        intro_form(occupations)

if prompt:
    # display user messages and save it to the chat history
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # display AI messages and save it to the chat history
    with st.chat_message("assistant"):
        with st.spinner("Waiting for a response"):
            # Get KB for skills and courses 
            skills = querySkill(kb_id, aws_key, aws_secret, st.session_state.job, prompt)
            courses = queryCourse(kb_id, aws_key, aws_secret, st.session_state.job, prompt)
            print(skills)
            print(" --- ")
            print(" --- ")
            print(courses)
            print(" --- ")
            print(" --- ")

            # Query LLM with context
            response = LLM(aws_key, aws_secret, prompt, st.session_state.cv, courses, skills, st.session_state.job, st.session_state.exp)
            print(response)
        if response:
            st.markdown(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response if response else "Error in response"})