import streamlit as st
import boto3
import json
from textractProcessor import textractProcessor

import configparser
credents = configparser.ConfigParser()
credents.read_file(open('credential.conf'))

#Reading in the credentials into Python variables. No can see them
aws_key = credents["AWS"]["KEY"]
aws_secret = credents["AWS"]["SECRET"]
region = credents["AWS"]["REGION"]

# Initialize bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)

# Initialize S3 client
s3_client = boto3.client(service_name = 's3', aws_access_key_id=aws_key,
                            aws_secret_access_key=aws_secret, region_name=region)
bucket_name = 'unchanged-cvs'

# Function to upload a file to S3 with a key
def upload_file_to_s3(file, key):
    result = s3_client.put_object(Bucket=bucket_name, Key=key, Body=file)
    print(result)
    if result['ResponseMetadata']['HTTPStatusCode'] == 200:
       st.write("File uploaded successfully!")
       return True
    else:
       st.write("File uploaded failed!")
       return False

def call_bedrock_api(input_text):
    try:
        response = bedrock_runtime.invoke_model(
            modelId="amazon.titan-text-express-v1:0:8k",
            ContentType="application/json",
            Body=json.dumps({"input": input_text}),
        )
        result = json.loads(response["Body"].read())
        return result
    except Exception as e:
        st.error(f"Error calling Bedrock API: {e}")
        return None

def promptFlow():
    bedrock_agent_runtime = boto3.client(service_name = 'bedrock-agent-runtime',aws_access_key_id=aws_key,
                            aws_secret_access_key=aws_secret, region_name = 'us-east-1')
    response = bedrock_agent_runtime.invoke_flow(
    flowIdentifier = 'B378LH9NPQ',
    flowAliasIdentifier = 'LG7V98CKZP',
    inputs = [
        { 
            "content": { 
                "document": "Summarize key information for"
            },
            "nodeName": "FlowInputNode",
            "nodeOutputName": "document"
        }
    ])
    event_stream = response["responseStream"]
    for event in event_stream:
        print(json.dumps(event, indent=2, ensure_ascii=False))

def intro_form():
    with st.form("Employee Details"):
        user_name = st.text_input("Name")
        user_cv = st.file_uploader("Upload your CV below", type=["pdf", "docx"])
        submitted = st.form_submit_button("Submit")
    if submitted and user_name.strip() and user_cv:
        uploaded = upload_file_to_s3(user_cv, user_name)
        if(uploaded):
            # file uploaded to s3, proceed to use textract on s3 file
            textract = textractProcessor(bucket_name, user_name)
            rawCV = textract.processDocument()
            st.session_state.show_form = False
            # once we got the context we can further call our prompt flow 

    else:
        if submitted:
            st.warning('Please enter correct details', icon="⚠️")

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
        intro_form()

if prompt:
    # display user messages and save it to the chat history
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # display AI messages and save it to the chat history
    with st.chat_message("assistant"):
        # user_cv = st.file_uploader("Upload your CV", type=["pdf", "docx"])
        with st.spinner("Waiting for a response"):
            response = call_bedrock_api(prompt)
        if response:
            st.markdown(response)

    st.session_state.chat_history.append({"role": "assistant", "content": prompt})
