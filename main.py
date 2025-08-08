from fastapi import FastAPI
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import os
import openai
from supabase import create_client

app = FastAPI()

# Load environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not all([OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY]):
    raise Exception("Missing one or more environment variables: OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")

openai.api_key = OPENAI_API_KEY
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

PDF_PATH = './Final_amended_after_printing_EN_PHC_Guide_September_25_2c_2015.pdf'


def extract_text_from_pdf(path: str) -> str:
    doc = fitz.open(path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text


def embed_text(text: str):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-3-large"
    )
    return response['data'][0]['embedding']


@app.post("/embed-pdf")
async def embed_pdf():
    try:
        text = extract_text_from_pdf(PDF_PATH)
        embedding = embed_text(text)

        # Insert into supabase
        data, error = supabase.table('pdf').insert({
            'session_id': 'default-session',
            'content': text,
            'content_hash': 'hash123',  # You may want to use a real hash function here
            'message': {},              # optional extra
            'embedding': embedding,
            'metadata': {},
            'file_name': 'Final_amended_after_printing_EN_PHC_Guide.pdf'
        }).execute()

        if error:
            return JSONResponse(status_code=500, content={"error": str(error)})

        return {"message": "Embedded and saved successfully."}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
