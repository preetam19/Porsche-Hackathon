import json
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import os 
import re
from dotenv import load_dotenv
import sys
from langdetect import detect
from langchain.llms import AzureOpenAI
from langchain.chat_models import AzureChatOpenAI
from langchain import OpenAI, LLMChain
from langchain import PromptTemplate
file_path = sys.argv[1]

folders = ['data', 'results']

for folder in folders:
    os.makedirs(folder, exist_ok=True)
load_dotenv()

OPENAI_API_TYPE = os.environ.get('OPENAI_API_TYPE')
OPENAI_API_BASE = os.environ.get('OPENAI_API_BASE')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_API_VERSION = os.environ.get('OPENAI_API_VERSION')

embeddings = OpenAIEmbeddings(deployment="porsche_hackathon_ada2", chunk_size=1)
loader = PyPDFLoader(file_path)
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


entire_description = format_text('/app/data/scraped_jobs_base.json')


def get_recommendation(job_files, resume, output_path):    
    faiss = FAISS.from_texts(job_files, embeddings)
    recommendation_list = faiss.similarity_search(resume[0].page_content, k=5)
    recommendation_list = [file.page_content for file in recommendation_list]
    resume_recommendations = {
        'resume': resume[0].page_content,
        'recommendations': recommendation_list
    }
    lang = detect(resume[0].page_content)
    with open(output_path, 'w') as f:
        json.dump(resume_recommendations, f)
    return recommendation_list, lang, resume_recommendations
    
recomendation_list,lang, full_profile = get_recommendation(job_files=entire_description, resume=resume, output_path='/data/results.json')

def get_rankings(profile):
    print('I AM INSIDE THE GET RANKING')
    resume =profile['resume']
    print(len(profile))
    job_des = profile['recommendations'][0] #hardcoding here, 
    llm = AzureOpenAI(
    # deployment_name="porsche_hackathon_gpt4",
            model_name="gpt-4",
            deployment_id = "porsche_hackathon_gpt4"
            )
    template = """Given the Resume and Job description, your task is to score the applicant based on the Resume with respective to the job description.
    Give the score  out of 10, also provide why the applicant is fit for the give role and why the applicant might not be the fit the job.
    Additionally, provide skill gap analysis of the applicant based on job description.
    Please akways follow the following format -
    Applicant Name: 
    Score: 
    Strengths:
    Possible Weakness:
    Additional Comments:
    resume: {resume}
    job_description: {job_des} """

    prompt = PromptTemplate(template=template, input_variables=["resume","job_des"])
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    result = llm_chain.run({'resume':resume,'job_des':job_des})

    return result

print(full_profile)
x = get_rankings(full_profile)


def extract_info_from_text(text):
    # Using regular expressions to extract information
    patterns = {
        "Applicant Name": r"Applicant Name: ([^\n]+)",
        "Score": r"Score: ([^\n]+)",
        "Strengths": r"Strengths:\n([\s\S]+?)\n\n",
        "Potential Weakness": r"Potential Weakness:\n([\s\S]+?)\n\n",
        "Additional Comments": r"Additional Comments:\n([\s\S]+)"
    }
    
    data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            data[key] = match.group(1)

    # Convert dictionary to JSON
    json_data = json.dumps(data, indent=4)

    return json_data

    
    # except AttributeError:
    #     return "Unable to extract all the required information from the text."
json_profile = extract_info_from_text(x)
with open('/data/rankings.json', 'w') as f:
    json.dump(json_profile, f)
def process_recommendations(recommendation_list):
    extracted_data_v3 = []
    for index, rec_str in enumerate(recommendation_list, start=1):
        lines = rec_str.split("\n")
        title = next((line.split(":")[1].strip().rstrip(',') for line in lines if "Title:" in line), 'N/A')
        code = next((line.split(":")[1].strip() for line in lines if "Code:" in line), 'N/A').replace("J", "Job ID: J")
        location = next((line.split(":")[1].strip() for line in lines if "Location:" in line), 'N/A').replace("\\78", " 78")
        
        extracted_data_v3.append(f"Recommendation {index}: Title: {title}, Code ({code}), Location: {location}")

    formatted_output_v3 = "\n".join(extracted_data_v3)

    details_list = []

    for idx, element in enumerate(recommendation_list, start=1):
        entry_type_match = re.search(r'Entry Type: (.+)', element)
        entry_type = entry_type_match.group(1) if entry_type_match else "N/A"

        tasks_match = re.search(r'Tasks:\n(.*?)(\n\n|$)', element, re.DOTALL)
        tasks = tasks_match.group(1).split("\n- ")[1:] if tasks_match else ["N/A"]

        requirements_match = re.search(r'Requirements:\n(.*?)(\n\n|$)', element, re.DOTALL)
        requirements = requirements_match.group(1).split("\n- ")[1:] if requirements_match else ["N/A"]

        details = f"Recommendation {idx}:\n"  
        details += f"Entry Type: {entry_type}\n"
        details += "Tasks:\n" + "\n".join(tasks) + "\n\n"
        details += "Requirements:\n" + "\n".join(requirements)
        details_list.append(details)

    context = " ".join(details_list)
    return formatted_output_v3, context


response, context=process_recommendations(recomendation_list)

with open('/data/bot_response.json', 'w') as f:
    json.dump({"Response": response, "Context": context, "Language": lang}, f)
    
     # text = 'recommendataion: {i} , job title: {i['']}, job Id , compan # for idx,i in enumerate(recoomendation_list):
     # 
     #  #     f'recommendataion: {3} , job title: {i['']}, job Id , compan


