# -*- coding: utf-8 -*-
"""Individual_Project_23200441.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1waZBv2LQtT3VfqATW1XU2Izrh2WU4qUz
"""

!pip install openai
!pip install tiktoken
!pip install  cohere


import os, sys, cohere, tiktoken
from openai import OpenAI
from google.colab import userdata
import time

from google.colab import drive
drive.mount('/content/drive')

"""# Attempt 1: Simple Implementation"""

client = OpenAI(api_key = userdata.get('API_KEY'))

assistant = client.beta.assistants.create(
    name="Football Assistant",
    instructions="Provide the latest information on football matches, player stats, and team news.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4"
)
print("Assistant created successfully:", assistant.id)

# Create a thread for the conversation
thread = client.beta.threads.create()
print("Thread created successfully:", thread.id)

# Get the user's football-related question via input (e.g., in a web form or console input)
user_question = input("Please enter your football query: ")

# Add the user's question to the thread
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=user_question
)
print("Message added successfully:", message.id)

# Initiate a run to process the user's question
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id
)
print("Run initiated successfully:", run.id)

# Monitor the run's completion and fetch messages
while True:
    lrun = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    if lrun.status == 'in_progress':
        time.sleep(2)  # Wait for 2 seconds before checking again
    else:
        break

# Fetch messages from the thread after the run is complete
messages = client.beta.threads.messages.list(thread_id=thread.id)
for message in messages.data:
    print(message.content)  # Display the assistant's responses



"""# Attempt 2: Simple Implementation with Dataset"""

assistant = client.beta.assistants.create(
    name="Football Assistant",
    instructions= "Provide the latest information on football matches, player stats, and team news for Real Madrid.",
    model="gpt-3.5-turbo",
    tools=[{"type": "file_search"}],
)

vector_store = client.beta.vector_stores.create(name="Fixtures")

# files for upload to OpenAI
file_paths = ["/content/drive/MyDrive/Gen_AI_Project_Files/Data.txt"]
file_streams = [open(path, "rb") for path in file_paths]

file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)

assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

# Upload the user provided file to OpenAI
message_file = client.files.create(
  file=open("/content/drive/MyDrive/Gen_AI_Project_Files/Data.txt", "rb"), purpose="assistants"
)

# Create thread and attach the file to the message
thread = client.beta.threads.create(
  messages=[
    {
      "role": "user",
      "content": "Hello, give me matches where real madrid played barcelona",
      "attachments": [
        { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
      ],
    }
  ]
)
print(thread.tool_resources.file_search)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, assistant_id=assistant.id
)

messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

message_content = messages[0].content[0].text
annotations = message_content.annotations
citations = []
for index, annotation in enumerate(annotations):
    message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
    if file_citation := getattr(annotation, "file_citation", None):
        cited_file = client.files.retrieve(file_citation.file_id)
        citations.append(f"[{index}] {cited_file.filename}")

print(message_content.value)

"""#Attempt 3: Assistant using a dataset with continuous conversational abilities"""

assistant = client.beta.assistants.create(
    name="Football Assistant",
    instructions="Provide the latest information on football matches, player stats, and team news for Real Madrid.",
    model="gpt-3.5-turbo",
    tools=[{"type": "file_search"}],
)

# Create a vector store and upload your data file
vector_store = client.beta.vector_stores.create(name="Fixtures")
file_path = "/content/drive/MyDrive/Gen_AI_Project_Files/Data.txt"

# Open file once and reuse the file stream
with open(file_path, "rb") as file_stream:
    # Upload and index files in the vector store
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=[file_stream]
    )

# Update the assistant to use the newly created vector store
assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

# Create a message file for attachment to messages
with open(file_path, "rb") as file_stream:
    message_file = client.files.create(
        file=file_stream, purpose="assistants"
    )

# Continuous conversation loop with data-enabled responses
while True:
    user_query = input("Please enter your football query or type 'exit' to end: ")
    if user_query.lower() in ['exit', 'done']:
        print("Ending the conversation. Thank you!")
        break
    else:
        # Create thread and attach the file to the message
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": user_query,
                    "attachments": [
                        {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
                    ],
                }
            ]
        )

        # Initiate a run to process the user's question with data access
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant.id
        )

        # Retrieve the run's results and print the assistant's response
        messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
        for message in messages:
            if message.role == 'assistant':  # Filter out only assistant's messages
                print("Assistant's Response:", message.content)
                break
        print("Do you have any other queries?")

"""# Attempt 4: Assistant using a dataset with continuous conversational abilities with complex prompts such as RAG and COT"""

# Create an assistant with capabilities for file search
assistant = client.beta.assistants.create(
    name="Football Assistant",
    instructions="Analyze and provide detailed insights on football matches, player stats, and team news for Real Madrid, including historical data comparison and trend analysis.",
    model="gpt-3.5-turbo",
    tools=[{"type": "file_search"}],
)

# Create a vector store to enable efficient data search
vector_store = client.beta.vector_stores.create(name="Fixtures")
file_path = "/content/drive/MyDrive/Gen_AI_Project_Files/Data.txt"

# Open the file once and use the file stream to upload and index the file in the vector store
with open(file_path, "rb") as file_stream:
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=[file_stream]
    )

# Update the assistant to use the newly created vector store
assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

# Create a message file for attachment to messages using the same data file
with open(file_path, "rb") as file_stream:
    message_file = client.files.create(
        file=file_stream, purpose="assistants"
    )

def process_query_with_cot_rag(user_query):
    """Process user queries using Chain of Thought and Retrieval-Augmented Generation."""
    # Create a thread with an enhanced prompt for CoT and attach the file
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": f"First, let's retrieve relevant data for: {user_query}. Analyze the data to extract meaningful insights and comparisons.",
                "attachments": [{"file_id": message_file.id, "tools": [{"type": "file_search"}]}],
            }
        ]
    )

    # Initiate a run to process the user's question with data access
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant.id
    )

    # Retrieve and format the assistant's responses
    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
    for message in messages:
        if message.role == 'assistant':
            print("Assistant's CoT and RAG Response:", message.content)
            break

# Continuous conversation loop with data-enabled responses
while True:
    user_query = input("Please enter your football query or type 'exit' to end: ")
    if user_query.lower() in ['exit', 'done', 'no']:
        print("Ending the conversation. Thank you!")
        break
    else:
        process_query_with_cot_rag(user_query)
        print("Do you have any other queries?")

"""Sample COT and RAG examples:"""

# Assume all imports and basic setup as previously defined

def engage_fan_conversation(query):
    if 'prediction' in query.lower():
        return "What's your prediction for today's game? Here's some stats to help you decide!"
    elif 'trivia' in query.lower():
        return "Time for some trivia! Who scored the winning goal in last year's fixture?"
    elif 'learn' in query.lower():
        return "Let's learn about football tactics. Today's topic: Total Football. Ready to start?"

# Enhance the conversation loop
while True:
    user_query = input("Please enter your football query or type 'exit' to end: ")
    if user_query.lower() in ['exit', 'done']:
        print("Ending the conversation. Thank you!")
        break
    else:
        engagement_response = engage_fan_conversation(user_query)
        print("Assistant's Response:", engagement_response)
        print("Do you have any other queries?")