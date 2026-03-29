import os
from openai import OpenAI
import mimetypes
import sys
import base64
import time

API_KEY_ENV_VAR = "OPENAI_API_KEY"


def read_api_key():
    api_key = os.getenv(API_KEY_ENV_VAR, "").strip()
    if api_key:
        return api_key

    print(
        "Error: OPENAI_API_KEY is not set.\n"
        "Set it before running this script.\n"
        "Example:\n"
        "  export OPENAI_API_KEY='your-api-key-here'\n"
        "You can also put OPENAI_API_KEY in your local .env and load it into the environment.\n"
        "Then re-run the script."
    )
    sys.exit(1)

# Function to read the caption prompt from the file
def read_caption_prompt(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: Caption prompt file not found at {file_path}")
        sys.exit(1)
        
# Function to encode an image to a base64 string
def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            mime_type, _ = mimetypes.guess_type(image_path)

            if not mime_type or not mime_type.startswith("image"):
                raise ValueError(f"Unsupported file type: {image_path}")
                
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image to base64: {e}")
        return None
        
       
# Process a message
def process_message(client, assistant, thread, image_path, caption_prompt):
    image = client.files.create(
        file=open(image_path, "rb"),
        purpose="assistants"
    )

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=[
            {
                "type": "text", 
                "text": caption_prompt
            },
            {
                "type": "image_file", 
                "image_file": {
                    "file_id": image.id, "detail": "low"
                }
            }
        ]
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # Wait for the answer
    while not run.status == "completed":
        print("Waiting for answer...")
        time.sleep(1)

        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

    # Get the response  
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    try:
        result = messages.data[0].content[0].text.value
        print(result)
        return result

    except Exception as e:
        print(e)
        return ""

# Function to process the directory and generate captions for images
def process_directory(directory):
    caption_prompt_file = os.path.join(".", "Categorize_Prompt.txt")

    # Read API key and caption prompt
    api_key = read_api_key()
    caption_prompt = read_caption_prompt(caption_prompt_file)

    # Supported image extensions
    image_extensions = ['.png', '.jpg']
    
    # Open a client for ChatGDP
    client = OpenAI(api_key=api_key)
    assistant = client.beta.assistants.create(
        name="AI image prompter",
        instructions="You are an assistant, helping creating prompts for the AI image generator FLUX.",
        model="gpt-4o"
    )
    
    # Create the thread
    thread = client.beta.threads.create()
    print(thread)
    
    for file in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, file)) and os.path.splitext(file)[1].lower() in image_extensions:
            
            image_path = os.path.join(directory, file)
            
            result = process_message(client, assistant, thread, image_path, caption_prompt)
            
            if(result != ""):
                # Write to output file with UTF-8 encoding
                output_text_path = os.path.splitext(image_path)[0] + ".txt"   
                with open(output_text_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(result)
                
                print(f"Caption saved to: {output_text_path}") 
                
            
# Entry point of the script
def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]

    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)

    process_directory(directory)

if __name__ == "__main__":
    main()
