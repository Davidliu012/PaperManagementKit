import pymupdf  # PyMuPDF
import os
from openai import OpenAI
from dotenv import load_dotenv
import argparse
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

def get_all_folder_names(directory):
    return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]

def write_to_mdfile(summary, category, title, paper_folder, paper_website):
    add_bullet_point(category, paper_website, f"{paper_folder}/description.md", prefix=title)
    add_bullet_point(title, summary, f"{paper_folder}/{category}/{category}.md", prefix="Summary")

def add_bullet_point(section, summary, mdfile_path, prefix=""):
    # Read the content of the file
    with open(mdfile_path, 'r') as file:
        lines = file.readlines()

    # Find the section to add the new point
    section_header = f"### {section}\n"
    if section_header not in lines:
        print(f"Section '{section}' not found in {mdfile_path}.")
        # create the section
        lines.append(section_header)

    section_index = lines.index(section_header)
    # Find the next section or the end of the file
    next_section_index = len(lines)
    for i in range(section_index + 1, len(lines)):
        if lines[i].startswith('### '):
            next_section_index = i
            break

    # Count the existing bullet points in the section
    bullet_count = 0
    for i in range(section_index + 1, next_section_index):
        if lines[i].strip().startswith('- '):
            bullet_count += 1

    # Add the new bullet point
    if prefix == "":
        new_line = f" - {bullet_count + 1}. {summary}\n"
        lines.insert(next_section_index, new_line)
    else:
        new_line = f" - {prefix}:\n {summary}\n"
        lines.insert(next_section_index, new_line)

    # Write the updated content back to the file
    with open(mdfile_path, 'w') as file:
        file.writelines(lines)

    print(f"Added new point to section '{section}' in {mdfile_path}.")

def main(paper_folder):
    # Find the latest PDF file in the current directory
    pdf_path = find_latest_pdf("new_papers/")
    if not pdf_path:
        print("No PDF files found in the current directory.")
        return
    
    paper_name = pdf_path.split("/")[-1].split(".")[0]

    paper_website = input(f"Enter the website of the paper {paper_name}: ")
    
    # Extract text from the first two pages of the PDF
    extracted_text = extract_text_from_pdf(pdf_path)

    folder_names = get_all_folder_names(paper_folder)
    num_categories = len(folder_names)
    application_prompt = f"Please help me summarize the main contribution of the following paper within 3 sentences, categorize this paper into one of the {num_categories} categories, and give it a short title: \n"
    for i, folder_name in enumerate(folder_names):
        application_prompt += f"{i+1}. {folder_name}\n"
    application_prompt += "Your response should have 3 section, one start with 'Summary:', one start with 'Category:', and one start with 'Title:'. All your resonse should be written in normal font!\n"
    application_prompt += "\nPaper: \n"

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

    summary = response.split("Category:")[0].split("Summary:")[1].strip()
    category = response.split("Title:")[0].split("Category:")[1].strip()
    title = response.split("Title:")[1].strip()

    write_to_mdfile(summary, category, title, paper_folder, paper_website)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize the main contribution of the latest PDF file in the current directory.")
    parser.add_argument("-f", "--folder", type=str, default="LLM_papers", help="Directory containing PDF files.")
    args = parser.parse_args()
    paper_folder = args.folder + "/"
    main(paper_folder)