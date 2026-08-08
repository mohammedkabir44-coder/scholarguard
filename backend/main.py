"""
ScholarGuard API
Academic Integrity Platform - Commercial-Ready SaaS
"""

import os
import hashlib
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import shutil
import uuid
import jwt
from passlib.context import CryptContext
from fpdf import FPDF

from database import get_db, init_db, engine, Base
from models import User, Submission
from services.file_parser import extract_text_from_file
from services.analyzer import analyze_document

app = FastAPI(title="ScholarGuard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "scholarguard-secret-key-change-in-production-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
PDF_FOLDER = "reports"
if not os.path.exists(PDF_FOLDER): os.makedirs(PDF_FOLDER)

Base.metadata.create_all(bind=engine)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = hashlib.sha256(plain_password.encode("utf-8")).hexdigest().encode("utf-8")
    return pwd_context.verify(pwd_bytes, hashed_password)

def get_password_hash(password: str) -> str:
    pwd_bytes = hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")
    return pwd_context.hash(pwd_bytes)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Query(...), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
    except jwt.PyJWTError: raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None: raise credentials_exception
    return user

@app.get("/")
def root():
    return {"message": "ScholarGuard API is running"}

class RegisterRequest(BaseModel):
    email: str
    password: str

@app.post("/api/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user: raise HTTPException(status_code=400, detail="Email already registered")
        hashed_password = get_password_hash(request.password)
        new_user = User(email=request.email, hashed_password=hashed_password, full_name="")
        db.add(new_user); db.commit(); db.refresh(new_user)
        return {"message": "User registered", "access_token": create_access_token(data={"sub": request.email}), "user": new_user.to_dict()}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "access_token": create_access_token(data={"sub": request.email}), "user": user.to_dict()}

@app.post("/api/upload")
async def upload_assignment(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        allowed = [".pdf", ".docx", ".doc", ".txt", ".rtf"]
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed: raise HTTPException(400, "File type not allowed")
        
        sub_id = str(uuid.uuid4())[:8]
        file_path = os.path.join(UPLOAD_FOLDER, f"{sub_id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        text = extract_text_from_file(file_path)
        analysis = analyze_document(text, file.filename)
        
        sub = Submission(user_id=current_user.id, file_name=file.filename, similarity_score=analysis["similarity_score"], ai_risk_score=analysis["ai_risk_score"], ai_confidence=analysis["ai_confidence"], recommendation=analysis["recommendation"], matched_sources=analysis["matched_sources"], text_content=text)
        db.add(sub); db.commit(); db.refresh(sub)
        
        return {"id": sub.id, "file_name": sub.file_name, "uploaded_at": sub.uploaded_at.isoformat(), "similarity_score": sub.similarity_score, "ai_risk_score": sub.ai_risk_score, "ai_confidence": sub.ai_confidence, "status": "completed", "recommendation": sub.recommendation, "matched_sources": sub.matched_sources}
    except HTTPException: raise
    except Exception as e: print("UPLOAD ERROR:", e); raise HTTPException(500, str(e))

@app.get("/api/reports")
def get_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subs = db.query(Submission).filter(Submission.user_id == current_user.id).order_by(Submission.uploaded_at.desc()).all()
    return {"total_reports": len(subs), "reports": [{"id": s.id, "file_name": s.file_name, "uploaded_at": s.uploaded_at.isoformat(), "similarity_score": s.similarity_score, "ai_risk_score": s.ai_risk_score} for s in subs]}

@app.get("/api/reports/{submission_id}/pdf")
def download_report_pdf(submission_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = db.query(Submission).filter(Submission.id == submission_id, Submission.user_id == current_user.id).first()
    if not sub: raise HTTPException(404, "Not found")
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"ScholarGuard Report: {sub.file_name}", 0, 1)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Similarity: {sub.similarity_score}%", 0, 1)
    pdf.cell(0, 10, f"AI Risk: {sub.ai_risk_score}%", 0, 1)
    pdf.cell(0, 10, f"Recommendation: {sub.recommendation}", 0, 1)
    
    path = os.path.join(PDF_FOLDER, f"report_{sub.id}.pdf")
    pdf.output(path)
    return FileResponse(path, filename=f"report_{sub.id}.pdf", media_type="application/pdf")

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("ScholarGuard API Starting...")
    print(f"JWT Secret: {'Configured' if SECRET_KEY != 'scholarguard-secret-key-change-in-production-2025' else 'Using default'}")
    print("=" * 60)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
