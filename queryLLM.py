import boto3
import json

def LLM(aws_key, aws_secret, userQuery, cv, courseKB, skillKB, job, exp):
    print("query: " + userQuery)
    print("cv: " + cv)
    print("courseKB: " + courseKB)
    print("skillKB: " + skillKB)
    # when cv is empty
    prompt = ''
    if cv.strip() == '':
        prompt = (
        f"When looking for courses to recommend you are instructed to only use the following {courseKB}. When looking for skills to recommend you are instructed to use only the following {skillKB}."
        f" As an Employee Mentor, you provide a tailored training recommendation by listening to the following user demand {userQuery}. You customize training recommendation based on user desired occupation and recommend skills and courses suitable for user experience level and capabilities. To build your training recommendation you will search for essential skills and essential courses by following instruction given to you. Structure your training recommendation by first stating the goal of training programmme which recognise user experience and capability. Afterward, list down those skills and courses separately with its respective desciption sequentially with proper indentation."
        f" All courses listed must mention its respective summary, url, rating, level and duration."
        f" Lastly, you will suggest a roadmap suggest which courses to take first and how to go about learning all the courses recommended to help user stay committed to the training recommendation."
        f" All skills and courses must show reference to source provided."
        f" If you are not confident in your answer or cannot find relevant information, please indicate that. Do not make up any information; only refer to the provided data."
        )
    else:
        prompt = (
        f"When looking for courses to recommend you are instructed to only use the following {courseKB}. When looking for skills to recommend you are instructed to use only the following {skillKB}. User desired aspiration, experience level, experience, goal and capability can be found in the following {cv}"
        f" As an Employee Mentor, you provide a tailored training recommendation by listening to the following user demand {userQuery}. You customize training recommendation based on user desired occupation and recommend skills and courses suitable for user experience level and capabilities. To build your training recommendation you will search for essential skills and essential courses by following instruction given to you. Structure your training recommendation by first stating the goal of training programmme which recognise user experience and capability. Afterward, list down those skills and courses separately with its respective desciption sequentially with proper indentation."
        f" All courses listed must mention its respective summary, url, rating, level and duration."
        f" Lastly, you will suggest a roadmap suggest which courses to take first and how to go about learning all the courses recommended to help user stay committed to the training recommendation."
        f" All skills and courses must show reference to source provided."
        f" If you are not confident in your answer or cannot find relevant information, please indicate that. Do not make up any information; only refer to the provided data."
        )
    print(prompt)

    # Initialize bedrock client
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret
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