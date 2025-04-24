#!/usr/bin/env python3
import os

from dotenv import load_dotenv
from openai import OpenAI


def main():
    # Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    model = "gpt-3.5-turbo"

    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        return

    # Initialize the v1 client with your key
    client = OpenAI(api_key=api_key)

    # Upload the file to OpenAI
    with open("training.jsonl", "rb") as file:
        response = client.files.create(
            file=file,
            purpose="fine-tune"
        )
    file_id = response.id
    print(f"File uploaded successfully. File ID: {file_id}")

    # 4) Kick off the fine-tune: note we pass the file *ID*, not the local path
    job = client.fine_tuning.jobs.create(
        training_file=file_id,
        model=model)

    print("Started fine-tune job:", job.id)

if __name__ == "__main__":
    main()