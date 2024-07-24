import boto3
import json

def LLM(aws_key, aws_secret, userQuery, cv, courseKB, skillKB):
    # Initialize bedrock client
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret
    )

    prompt = (
    f"As an Employee Mentor, you provide a tailored training recommendation by listening to what is their career aspiration, goal at {userQuery} "
    f"and customize training recommendation based on user desired occupation and recommend courses suitable for user level based on their experiences and capabilities at {cv}. To build your training recommendation you will use {skillKB} "
    f"to look for essential skills and {courseKB} to look for essential courses. Structure your training recommendation by firstly stating the goal of training programmme which recognise user experience and capability and then list those skill and course you found sequentially."
    f"All skills and courses must show reference to the source taken. If you are not confident in your answer or cannot find relevant information, please indicate that. Do not make up any information; only refer to the provided data."
    )
    
    # Model configuration
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    model_kwargs =  { 
        "max_tokens": 200000, "temperature": 0.1,
        "top_k": 250, "top_p": 0.999, "stop_sequences": ["\n\nHuman"],
    }

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "system": "You are a honest and helpful bot.",
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
        ],
    }
    body.update(model_kwargs)
    # Invoke
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
    )
    # Process and print the response
    result = json.loads(response.get("body").read()).get("content", [])[0].get("text", "")
    return result

