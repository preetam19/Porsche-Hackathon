import json
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import os 


from dotenv import load_dotenv

load_dotenv()

OPENAI_API_TYPE = os.environ.get('OPENAI_API_TYPE')
OPENAI_API_BASE = os.environ.get('OPENAI_API_BASE')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_API_VERSION = os.environ.get('OPENAI_API_VERSION')

embeddings = OpenAIEmbeddings(deployment="porsche_hackathon_ada2", chunk_size=1)
loader = PyPDFLoader("data/Final_Lebenslauf_10076.pdf")
resume = loader.load_and_split()

def convert_into_text(path):
    data = json.load(path)

def format_description(entry):
    tasks = "\n- ".join(entry["tasks"])
    requirements = "\n- ".join(entry["requirements"])

    return f"""Title: {entry['title']},
Code: {entry['code']}
Entry Type: {entry['entry_type']}
Location: {entry['location']}
Company: {entry['company']}
Tasks:
- {tasks}
Requirements:
- {requirements}"""


def format_text(path):
    with open(path, "r") as f:
        data = json.load(f)
    return [format_description(i) for i in data]


entire_description = format_text('data/scraped_jobs_base.json')

faiss = FAISS.from_texts(entire_description, embeddings)
recommendation_list = faiss.similarity_search(resume[0].page_content, k=5)
print(recommendation_list)
