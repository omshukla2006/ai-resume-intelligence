from pathlib import Path
from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .database import init_db, save_analysis
from .services.pdf_service import extract_text_from_pdf
from .services.matching_service import analyze_match
from .services.llm_service import generate_ai_analysis

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title='AI Resume Intelligence Platform', version='3.0')
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
templates = Jinja2Templates(directory=str(BASE_DIR / 'templates'))

@app.on_event('startup')
def startup():
    init_db()

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name='index.html', context={})

@app.get('/health')
def health():
    return {'status': 'ok', 'version': '3.0'}

@app.post('/api/analyze')
async def analyze(request: Request, resume: UploadFile = File(...), job_description: str = Form(...), job_title: str = Form('Target Role')):
    if not resume.filename.lower().endswith('.pdf'):
        return JSONResponse({'error': 'Please upload a PDF resume.'}, status_code=400)
    if not job_description.strip():
        return JSONResponse({'error': 'Please provide a job description.'}, status_code=400)
    pdf_bytes = await resume.read()
    try:
        resume_text = extract_text_from_pdf(pdf_bytes)
        if len(resume_text.strip()) < 80:
            return JSONResponse({'error': 'Very little text could be extracted from this PDF. Try a text-based PDF rather than a scanned image.'}, status_code=400)
        base = analyze_match(resume_text, job_description)
        ai = generate_ai_analysis(base, resume_text, job_description)
        result = {**base, **ai, 'filename': resume.filename, 'job_title': job_title.strip() or 'Target Role'}
        save_analysis(resume.filename, result['job_title'], result['score'], result)
        return result
    except Exception as exc:
        return JSONResponse({'error': str(exc)}, status_code=500)
