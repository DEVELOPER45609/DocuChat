import requests
import json

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmcmVzaEBleGFtcGxlLmNvbSIsImV4cCI6MTc4NTkxNzI3Nn0.gFwW-lC4X_nTmLaY8sFIPIdShRKTke7CAp2wPXwSLcE"

response = requests.post(
    "http://127.0.0.1:8000/api/chat/",
    headers={"Authorization": f"Bearer {TOKEN}"},   
    json={"question": "What is this document about and what frameworks are using in it and give me detail overview and compare it with other frameworks and what should i learn to improve my resume?"},
    stream=True,
)

full_answer = ""
for line in response.iter_lines():
    if line and line.startswith(b"data: "):
        event = json.loads(line[6:])
        if event["type"] == "token":
            full_answer += event["content"]
            print(event["content"], end="", flush=True)
        elif event["type"] == "citations":
            print("\n\nCITATIONS:", event["citations"])
            
            
            
        #   This is file use for testing the streaming response from 
        #   the FastAPI endpoint. It sends a POST request to the `/api/chat/` endpoint 
        #   with a question and streams the response, printing tokens as they are received and displaying citations at the end.  
        #   Like real-time chat applications, this approach allows for immediate feedback to the user while the server processes the request.