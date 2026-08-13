"""
Sawa Digital Tech Solutions API
Academic Integrity Platform - Commercial-Ready SaaS
"""

import os
import hashlib
import bcrypt
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
from fpdf import FPDF

from database import get_db, init_db, engine, Base, SessionLocal
from models import User, Submission
from services.file_parser import extract_text_from_file
from services.analyzer import analyze_document

app = FastAPI(title="Sawa Digital Tech Solutions API", version="3.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Accepts requests from ANY website (Vercel, Netlify, etc.)
    allow_credentials=False, # MUST be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "sawadigitaltech-secret-key-change-in-production-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@sawadigitaltech.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin123!")

# Use Render's persistent disk for file storage if available
RENDER_DISK_PATH = "/opt/render/project/src/data"
if os.path.exists(RENDER_DISK_PATH):
    UPLOAD_FOLDER = os.path.join(RENDER_DISK_PATH, "uploads")
    PDF_FOLDER = os.path.join(RENDER_DISK_PATH, "reports")
else:
    UPLOAD_FOLDER = "uploads"
    PDF_FOLDER = "reports"

if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(PDF_FOLDER): os.makedirs(PDF_FOLDER)

Base.metadata.create_all(bind=engine)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = hashlib.sha256(plain_password.encode("utf-8")).hexdigest().encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    pwd_bytes = hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")

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
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled. Contact your administrator.")
    return user

def get_current_admin(token: str = Query(...), db: Session = Depends(get_db)) -> User:
    user = get_current_user(token, db)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def seed_admin():
    db = next(get_db())
    try:
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not admin:
            db.add(User(email=ADMIN_EMAIL, hashed_password=get_password_hash(ADMIN_PASSWORD), full_name="Administrator", phone_number="000-000-0000", role="admin", is_active=True))
            db.commit()
            print(f"Admin account created: {ADMIN_EMAIL}")
            return
        # Ensure the existing admin has the correct role/password
        if admin.role != "admin":
            admin.role = "admin"
        if not verify_password(ADMIN_PASSWORD, admin.hashed_password):
            print(f"Admin password mismatch for {ADMIN_EMAIL} - resetting to configured password.")
            admin.hashed_password = get_password_hash(ADMIN_PASSWORD)
        db.commit()
        print(f"Admin account verified: {ADMIN_EMAIL}")
    finally:
        db.close()

def create_default_admin(db: Session):
    """Create the default admin account if it doesn't already exist."""
    admin = db.query(User).filter(User.email == "admin@scholarguard.com").first()
    if not admin:
        db.add(User(
            email="admin@scholarguard.com",
            hashed_password=get_password_hash("Admin123!"),
            full_name="Administrator",
            role="admin",
            is_active=True,
        ))
        db.commit()
    print("✅ Default admin account verified/created.")

@app.get("/")
def root(): return {"message": "Sawa Digital Tech Solutions API Premium v3.2 - Live Reference Engine", "version": "3.2.0"}

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    print("ADMIN LOGIN ATTEMPT:", request.email)
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account disabled. Contact your administrator.")
        return {"message": "Login successful", "access_token": create_access_token(data={"sub": request.email}), "user": user.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        print("LOGIN ERROR:", e)
        raise HTTPException(status_code=500, detail="Internal server error during login")

class AdminCreateUser(BaseModel):
    email: str
    password: str
    phone_number: str = ""

@app.post("/api/admin/users")
def admin_create_user(request: AdminCreateUser, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing: raise HTTPException(status_code=400, detail="Email already exists")
    new_user = User(email=request.email, hashed_password=get_password_hash(request.password), full_name="", phone_number=request.phone_number, role="user", is_active=True)
    db.add(new_user); db.commit(); db.refresh(new_user)
    return {"message": "User created", "user": new_user.to_dict()}

@app.get("/api/admin/users")
def admin_list_users(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id).all()
    return {"users": [u.to_dict() for u in users]}

@app.post("/api/admin/users/{user_id}/toggle")
def admin_toggle_user(user_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin": raise HTTPException(status_code=400, detail="Cannot disable an admin account")
    user.is_active = not user.is_active
    db.commit()
    return {"message": "User updated", "user": user.to_dict()}

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
        sub = Submission(
            user_id=current_user.id, file_name=file.filename,
            similarity_score=analysis["similarity_score"], ai_risk_score=analysis["ai_risk_score"],
            ai_confidence=analysis["ai_confidence"], recommendation=analysis["recommendation"],
            matched_sources=analysis["matched_sources"], text_content=text,
            word_count=analysis["word_count"], sentence_count=analysis["sentence_count"],
            burstiness_score=analysis["burstiness_score"], vocabulary_richness=analysis["vocabulary_richness"],
            improvement_tips=analysis["improvement_tips"]
        )
        db.add(sub); db.commit(); db.refresh(sub)
        return {
            "id": sub.id, "file_name": sub.file_name, "uploaded_at": sub.uploaded_at.isoformat(),
            "similarity_score": sub.similarity_score, "ai_risk_score": sub.ai_risk_score,
            "ai_confidence": sub.ai_confidence, "status": "completed",
            "word_count": sub.word_count, "sentence_count": sub.sentence_count,
            "burstiness_score": sub.burstiness_score, "vocabulary_richness": sub.vocabulary_richness,
            "recommendation": sub.recommendation, "matched_sources": sub.matched_sources,
            "improvement_tips": sub.improvement_tips
        }
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
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 15, "Sawa Digital Tech Solutions - Premium Analysis Report", 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Document: {sub.file_name}", 0, 1)
    pdf.cell(0, 6, f"Words: {sub.word_count} | Sentences: {sub.sentence_count}", 0, 1)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Core Metrics", 0, 1)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Plagiarism Similarity: {sub.similarity_score}%", 0, 1)
    pdf.cell(0, 8, f"AI Risk Probability: {sub.ai_risk_score}%", 0, 1)
    pdf.cell(0, 8, f"Burstiness (Human Variation): {sub.burstiness_score}%", 0, 1)
    pdf.cell(0, 8, f"Vocabulary Richness: {sub.vocabulary_richness}%", 0, 1)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Improvement Report", 0, 1)
    pdf.set_font("Arial", "", 11)
    tips = sub.improvement_tips if sub.improvement_tips else []
    for tip in tips:
        pdf.multi_cell(0, 6, f"- {tip}")
    pdf.ln(5)
    if sub.matched_sources:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Verified Matched Sources (Books / Web / Research)", 0, 1)
        pdf.set_font("Arial", "", 10)
        for src in sub.matched_sources:
            pdf.multi_cell(0, 5, f"Source: {src.get('source', 'Unknown')} | Match: {src.get('match_percent', 0)}%")
            if src.get("url"):
                pdf.set_text_color(0, 0, 255)
                pdf.multi_cell(0, 5, f"URL: {src.get('url')}")
                pdf.set_text_color(0, 0, 0)
    path = os.path.join(PDF_FOLDER, f"report_{sub.id}.pdf")
    pdf.output(path)
    return FileResponse(path, filename=f"report_{sub.id}.pdf", media_type="application/pdf")

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("Sawa Digital Tech Solutions API Premium v3.2 (Live Reference Engine) Starting...")
    print("=" * 60)
    seed_admin()
    db = SessionLocal()
    try:
        create_default_admin(db)
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
