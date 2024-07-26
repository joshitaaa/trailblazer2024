import boto3

def queryCourse(kb_id, aws_key, aws_secret, job, userQuery):
    # If job is empty
    if job.strip() == '':
        promptCourse = userQuery + " . Can u suggest all the courses that will help me ?"
    else:
        promptCourse = userQuery + ". User desired occupations is " + job + " . Can u suggest all the courses that will help me ?"
    print(promptCourse)

    # Create bedrock agent client
    bedrock_agent_client = boto3.client(service_name='bedrock-agent-runtime', aws_access_key_id=aws_key,
                                        aws_secret_access_key=aws_secret, region_name='us-east-1')
    # Retrieve courses needed for the occupation
    responseCourse_ret = bedrock_agent_client.retrieve(
        knowledgeBaseId=kb_id,
        nextToken='string',
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'filter': {
                    'orAll': [
                        {
                            'startsWith': {
                                'key': 'x-amz-bedrock-kb-source-uri',
                                'value': 's3://coursera-modified/'
                            }
                        },
                        {
                            'startsWith': {
                                'key': 'x-amz-bedrock-kb-source-uri',
                                'value': 's3://udemy-modified/'
                            }
                        },
                    ],
                },
                'numberOfResults': 20
            }
        },
        retrievalQuery={
            'text': promptCourse
        }
    )

    return repr(responseCourse_ret)

def querySkill(kb_id, aws_key, aws_secret, job, userQuery):
     # If job is empty
    if job.strip() == '':
        promptSkill = userQuery + " . Can u suggest all the skills that will help me ?"
    else:
        promptSkill = userQuery + ". User desired occupations is " + job + " . Can u suggest all the skills that will help me ?"
    print(promptSkill)

    # Create bedrock agent client
    bedrock_agent_client = boto3.client(service_name='bedrock-agent-runtime', aws_access_key_id=aws_key,
                                        aws_secret_access_key=aws_secret, region_name='us-east-1')
    # Retrieve skills needed for the occupation
    responseSkill_ret = bedrock_agent_client.retrieve(
        knowledgeBaseId=kb_id,
        nextToken='string',
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'filter': {
                    'startsWith': {
                        'key': 'x-amz-bedrock-kb-source-uri',
                        'value': 's3://esco-modified/'
                    }
                },
                'numberOfResults': 20
            }
        },
        retrievalQuery={
            'text': promptSkill
        }
    )

    return repr(responseSkill_ret)