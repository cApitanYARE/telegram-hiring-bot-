from faker import Faker

from docx import Document
from pypdf import PdfReader

from bot.create_bot import bot
from aiogram.types import Message

import re

# def get_random_person():
#     fake = Faker('en_US')

#     user = {
#         'name': fake.name(),
#         'address': fake.address(),
#         'phone_number': fake.phone_number(),
#         'job': fake.job()
#     }
#     return user


async def clear_text(text: str):
    if not text:
        return ""
        
    text = re.sub(r' {2,}', ' [WORD_BOUND] ', text)
    
    cleaned = re.sub(r'(?<=\b\w) (?=\w\b)', '', text)
    
    cleaned = cleaned.replace('[WORD_BOUND]', ' ')
    
    cleaned = re.sub(r'[\u200b\u200e\u200f\u202a\u202b\u202c\u202d\u202e\ufeff]', '', cleaned)
    
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        
    return cleaned.strip()

async def process_txt(file_path: str, message: Message):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    return text

async def process_docx(file_path: str, message: Message):
    doc = Document(file_path)
    full_text = []
    
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
        
    text_content = "\n".join(full_text)
    
    return text_content

async def process_pdf(file_path: str, message: Message):

    reader = PdfReader(file_path)
    full_text = ""
    
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    full_text = await clear_text(full_text)
    return full_text

async def clear_github_username(url: str):
    match = re.search(r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9-]+)', url)
    if match:
        return match.group(1)
    return None