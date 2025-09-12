import firebase_admin
from firebase_admin import credentials, firestore, storage
import requests
from io import BytesIO
import mimetypes
from PyPDF2 import PdfReader
import mammoth
import base64
from groq import Groq
import os

def download_file(file_url):
    response = requests.get(file_url)
    response.raise_for_status()
    content_type = response.headers.get('content-type')
    return response.content, content_type

def extract_text_from_pdf(pdf_bytes):
    reader = PdfReader(BytesIO(pdf_bytes))
    text = ''
    for page in reader.pages:
        text += page.extract_text() or ''
    return text

def extract_text_from_docx(docx_bytes):
    result = mammoth.extract_raw_text(BytesIO(docx_bytes))
    return result.value

def extract_text_from_image_with_groq(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY")
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "What's in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        model="meta-llama/llama-4-scout-17b-16e-instruct",
    )
    return chat_completion.choices[0].message.content

def process_file(file_url):
    file_bytes, content_type = download_file(file_url)
    extension = mimetypes.guess_extension(content_type)

    if extension in ['.pdf']:
        return extract_text_from_pdf(file_bytes)
    elif extension in ['.docx']:
        return extract_text_from_docx(file_bytes)
    elif extension in ['.jpg', '.jpeg', '.png']:
        return extract_text_from_image_with_groq(file_bytes)
    else:
        raise ValueError("Unsupported file type.")
