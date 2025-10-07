from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.security import HTTPBearer
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import json
import io
from emergentintegrations.llm.chat import LlmChat, UserMessage
import requests
import pdfplumber
import PyPDF2
from io import BytesIO

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Manuscript-TM DocWise API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer(auto_error=False)

# === PDF Processing Functions ===
async def extract_pdf_content(file_content: bytes, filename: str) -> str:
    """
    Advanced PDF extraction with tables and formatting preservation
    """
    try:
        # Use pdfplumber for advanced extraction with table support
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            extracted_text = f"[PDF Content from {filename}]\n\n"
            
            for page_num, page in enumerate(pdf.pages, 1):
                extracted_text += f"--- Page {page_num} ---\n"
                
                # Extract text with formatting
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
                
                # Extract tables if present
                tables = page.extract_tables()
                if tables:
                    extracted_text += "\n[TABLES FOUND ON THIS PAGE]\n"
                    for table_num, table in enumerate(tables, 1):
                        extracted_text += f"\nTable {table_num}:\n"
                        for row in table:
                            if row:  # Skip empty rows
                                # Join non-None cells with | separator
                                row_text = " | ".join([str(cell) if cell else "" for cell in row])
                                extracted_text += row_text + "\n"
                        extracted_text += "\n"
                
                extracted_text += "\n"
            
            return extracted_text
            
    except Exception as e:
        # Fallback to PyPDF2 for basic extraction
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            extracted_text = f"[PDF Content from {filename}] (Basic extraction)\n\n"
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                extracted_text += f"--- Page {page_num} ---\n"
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n\n"
            
            return extracted_text
            
        except Exception as fallback_error:
            # Final fallback
            return f"[PDF Content from {filename}]\n\nError extracting PDF content: {str(e)}\nFallback error: {str(fallback_error)}"

# === Models ===
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Prompt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PromptCreate(BaseModel):
    title: str
    content: str

class PromptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class DocumentAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    document_name: str
    prompt_id: str
    ai_model: str  # "gpt-5" or "claude-4-sonnet-20250514"
    extracted_text: str
    response: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnalysisRequest(BaseModel):
    prompt_id: str
    ai_model: str

class TextAnalysisRequest(BaseModel):
    prompt_id: str
    ai_model: str
    text_content: str
    document_name: str = "Text Input"

class SessionData(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    session_token: str

# === Authentication Helpers ===
ADMIN_EMAIL = "mueen.ahmed@gmail.com"

def is_admin_user(user):
    """Check if user is admin"""
    return user.email == ADMIN_EMAIL

async def get_current_user(request):
    """Get current user from session token"""
    # First check cookies
    session_token = request.cookies.get('session_token')
    
    # Fallback to Authorization header
    if not session_token:
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header[7:]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session in database
    session = await db.sessions.find_one({"session_token": session_token})
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Handle timezone-aware datetime comparison
    expires_at = session['expires_at']
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    elif expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
    user = await db.users.find_one({"id": session['user_id']})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user)

# === Authentication Routes ===
@api_router.post("/auth/session-data")
async def process_session_data(request: Request):
    """Process session ID from Emergent Auth"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Call Emergent Auth API
    try:
        response = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        response.raise_for_status()
        session_data = response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    # Check if user exists
    user = await db.users.find_one({"email": session_data['email']})
    if not user:
        # Create new user
        user_data = {
            "id": str(uuid.uuid4()),
            "email": session_data['email'],
            "name": session_data['name'],
            "picture": session_data.get('picture'),
            "created_at": datetime.now(timezone.utc)
        }
        result = await db.users.insert_one(user_data)
        user_data['_id'] = str(result.inserted_id)
        user = user_data
    
    # Create session
    session_token = str(uuid.uuid4())
    session_obj = {
        "id": str(uuid.uuid4()),
        "user_id": user['id'],
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.sessions.insert_one(session_obj)
    session_obj['_id'] = str(result.inserted_id)
    
    return {
        "user": user,
        "session_token": session_token
    }

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    """Register with username/password"""
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user (in production, hash the password)
    user = {
        "id": str(uuid.uuid4()),
        "email": user_data.email,
        "name": user_data.name,
        "password": user_data.password,  # In production: hash this
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.users.insert_one(user)
    user['_id'] = str(result.inserted_id)
    
    # Create session
    session_token = str(uuid.uuid4())
    session_obj = {
        "id": str(uuid.uuid4()),
        "user_id": user['id'],
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.sessions.insert_one(session_obj)
    session_obj['_id'] = str(result.inserted_id)
    
    # Convert ObjectId to string for serialization
    user_response = {k: str(v) if k == '_id' else v for k, v in user.items() if k != 'password'}
    
    return {
        "user": user_response,
        "session_token": session_token
    }

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    """Login with username/password"""
    user = await db.users.find_one({"email": login_data.email})
    if not user or user.get('password') != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    session_token = str(uuid.uuid4())
    session_obj = {
        "id": str(uuid.uuid4()),
        "user_id": user['id'],
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.sessions.insert_one(session_obj)
    session_obj['_id'] = str(result.inserted_id)
    
    # Convert ObjectId to string for serialization
    user_response = {k: str(v) if k == '_id' else v for k, v in user.items() if k != 'password'}
    
    return {
        "user": user_response,
        "session_token": session_token
    }

@api_router.post("/auth/logout")
async def logout(request: Request):
    """Logout user"""
    session_token = request.cookies.get('session_token')
    if session_token:
        await db.sessions.delete_one({"session_token": session_token})
    return {"success": True}

@api_router.get("/auth/me")
async def get_me(request: Request):
    """Get current user info"""
    user = await get_current_user(request)
    return user

# === Prompt Management Routes ===
@api_router.post("/prompts", response_model=Prompt)
async def create_prompt(prompt_data: PromptCreate, request: Request):
    """Create a new prompt - Admin only"""
    user = await get_current_user(request)
    
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    prompt = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "title": prompt_data.title,
        "content": prompt_data.content,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    await db.prompts.insert_one(prompt)
    return Prompt(**prompt)

@api_router.get("/prompts", response_model=List[Prompt])
async def get_prompts(request: Request):
    """Get all prompts for current user"""
    user = await get_current_user(request)
    
    prompts = await db.prompts.find({"user_id": user.id}).to_list(1000)
    return [Prompt(**prompt) for prompt in prompts]

@api_router.put("/prompts/{prompt_id}", response_model=Prompt)
async def update_prompt(prompt_id: str, prompt_data: PromptUpdate, request: Request):
    """Update a prompt"""
    user = await get_current_user(request)
    
    # Check if prompt exists and belongs to user
    existing = await db.prompts.find_one({"id": prompt_id, "user_id": user.id})
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Update fields
    update_data = {k: v for k, v in prompt_data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.prompts.update_one(
        {"id": prompt_id}, 
        {"$set": update_data}
    )
    
    updated_prompt = await db.prompts.find_one({"id": prompt_id})
    return Prompt(**updated_prompt)

@api_router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str, request: Request):
    """Delete a prompt"""
    user = await get_current_user(request)
    
    result = await db.prompts.delete_one({"id": prompt_id, "user_id": user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return {"success": True}

# === Document Analysis Routes ===
@api_router.post("/documents/analyze")
async def analyze_document(
    request: Request,
    file: UploadFile = File(...),
    analysis_data: str = Form(...)
):
    """Upload and analyze document"""
    user = await get_current_user(request)
    
    try:
        analysis_request = AnalysisRequest.model_validate_json(analysis_data)
    except Exception as e:
        logging.error(f"Analysis data parsing error: {e}")
        logging.error(f"Analysis data received: {analysis_data}")
        raise HTTPException(status_code=400, detail=f"Invalid analysis data: {str(e)}")
    
    # Check if prompt exists and belongs to user
    prompt = await db.prompts.find_one({
        "id": analysis_request.prompt_id,
        "user_id": user.id
    })
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read file content
    file_content = await file.read()
    
    # Advanced PDF extraction with tables and formatting
    extracted_text = await extract_pdf_content(file_content, file.filename)
    
    # Generate AI response
    try:
        # Initialize AI chat
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=str(uuid.uuid4()),
            system_message="You are an expert document analyzer. Provide detailed, comprehensive responses based on the document content and user prompts."
        )
        
        # Set model based on user selection
        if analysis_request.ai_model == "gpt-5":
            chat.with_model("openai", "gpt-5")
        elif analysis_request.ai_model == "claude-4":
            chat.with_model("anthropic", "claude-4-sonnet-20250514")
        else:
            raise HTTPException(status_code=400, detail="Invalid AI model")
        
        # Create analysis prompt
        analysis_prompt = f"""Document Content:
{extracted_text}

User Prompt: {prompt['content']}

Please analyze the document content according to the user prompt and provide a comprehensive, detailed response."""
        
        user_message = UserMessage(text=analysis_prompt)
        ai_response = await chat.send_message(user_message)
        
    except Exception as e:
        logging.error(f"AI analysis error: {e}")
        raise HTTPException(status_code=500, detail="AI analysis failed")
    
    # Save analysis result
    analysis = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "document_name": file.filename,
        "prompt_id": analysis_request.prompt_id,
        "ai_model": analysis_request.ai_model,
        "extracted_text": extracted_text,
        "response": str(ai_response),
        "created_at": datetime.now(timezone.utc)
    }
    await db.analyses.insert_one(analysis)
    
    return DocumentAnalysis(**analysis)

@api_router.get("/documents/analyses", response_model=List[DocumentAnalysis])
async def get_analyses(request: Request):
    """Get all analyses for current user"""
    user = await get_current_user(request)
    
    analyses = await db.analyses.find({"user_id": user.id}).sort("created_at", -1).to_list(1000)
    return [DocumentAnalysis(**analysis) for analysis in analyses]

@api_router.get("/documents/analyses/{analysis_id}/download")
async def download_analysis(analysis_id: str, request: Request):
    """Download analysis as text file"""
    user = await get_current_user(request)
    
    analysis = await db.analyses.find_one({"id": analysis_id, "user_id": user.id})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Create downloadable content
    content = f"""Document Analysis Report
================================

Document: {analysis['document_name']}
AI Model: {analysis['ai_model']}
Generated: {analysis['created_at']}

--- Analysis Response ---
{analysis['response']}

--- Extracted Text ---
{analysis['extracted_text']}
"""
    
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=analysis_{analysis_id}.txt"}
    )

# === Text Analysis Route ===
@api_router.post("/documents/analyze-text")
async def analyze_text(
    request: Request,
    analysis_request: TextAnalysisRequest
):
    """Analyze text content directly without file upload"""
    user = await get_current_user(request)
    
    # Check if prompt exists and belongs to user
    prompt = await db.prompts.find_one({
        "id": analysis_request.prompt_id,
        "user_id": user.id
    })
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Use text content directly
    extracted_text = f"[Text Content from {analysis_request.document_name}]\n\n{analysis_request.text_content}"
    
    # Generate AI response
    try:
        # Initialize AI chat
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=str(uuid.uuid4()),
            system_message="You are an expert document analyzer. Provide detailed, comprehensive responses based on the document content and user prompts."
        )
        
        # Set model based on user selection
        if analysis_request.ai_model == "gpt-5":
            chat.with_model("openai", "gpt-5")
        elif analysis_request.ai_model == "claude-4":
            chat.with_model("anthropic", "claude-4-sonnet-20250514")
        else:
            raise HTTPException(status_code=400, detail="Invalid AI model")
        
        # Create analysis prompt
        analysis_prompt = f"""Text Content:
{analysis_request.text_content}

User Prompt: {prompt['content']}

Please analyze the text content according to the user prompt and provide a comprehensive, detailed response."""
        
        user_message = UserMessage(text=analysis_prompt)
        ai_response = await chat.send_message(user_message)
        
    except Exception as e:
        logging.error(f"AI analysis error: {e}")
        raise HTTPException(status_code=500, detail="AI analysis failed")
    
    # Save analysis result
    analysis = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "document_name": analysis_request.document_name,
        "prompt_id": analysis_request.prompt_id,
        "ai_model": analysis_request.ai_model,
        "extracted_text": extracted_text,
        "response": str(ai_response),
        "created_at": datetime.now(timezone.utc)
    }
    await db.analyses.insert_one(analysis)
    
    return DocumentAnalysis(**analysis)

# === Health Check ===
@api_router.get("/")
async def root():
    return {"message": "Manuscript-TM DocWise API is running"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
