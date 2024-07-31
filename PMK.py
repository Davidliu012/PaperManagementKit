import pymupdf  # PyMuPDF
import os
from openai import OpenAI
from dotenv import load_dotenv
import glob

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    api_key=OPENAI_API_KEY,
)

def find_latest_pdf(directory):
    # Pattern to match all PDF files in the directory
    pdf_pattern = os.path.join(directory, "*.pdf")
    
    # List all PDF files in the directory
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        return None  # No PDF files found
    
    # Find the latest file based on modification time
    latest_pdf = max(pdf_files, key=os.path.getmtime)
    
    return latest_pdf

def extract_text_from_pdf(pdf_path, num_pages=2):
    # Open the PDF file
    document = pymupdf.open(pdf_path)
    text = ""

    # Extract text from the first 'num_pages' pages
    for page_num in range(min(num_pages, len(document))):
        page = document.load_page(page_num)
        text += page.get_text()
    
    return text

def get_gpt4_response(messages):
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Use GPT-4
        messages=messages,
        temperature=0.2,  # Low temperature for more coherent responses
    )
    return response.choices[0].message.content

def main():
    # Find the latest PDF file in the current directory
    pdf_path = find_latest_pdf("new_papers/")
    if not pdf_path:
        print("No PDF files found in the current directory.")
        return
    
    # Extract text from the first two pages of the PDF
    extracted_text = extract_text_from_pdf(pdf_path)
    application_prompt = "Please help me summarize the main contribution of the following paper within 5 sentences: \n"

    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": application_prompt}],
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": extracted_text}],
        },
    ]

    # Get response from GPT-4
    response = get_gpt4_response(messages)

    # Print the response
    print("GPT-4-mini Response:\n")
    print(response)

if __name__ == "__main__":
    main()