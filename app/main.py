from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBearer, HTTPBasicCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
from app import models, database
from jose import JWTError, jwt
from dotenv import load_dotenv
import secrets

load_dotenv()

app = FastAPI()
security = HTTPBasic()
security_bearer = HTTPBearer()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

models.Base.metadata.create_all(bind=database.engine)

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("ADMIN_USERNAME")
    correct_password = os.getenv("ADMIN_PASSWORD")
    
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials.username

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None

async def get_current_visitor(request: Request):
    token = request.cookies.get("visitor_token")
    if not token:
        return None
    
    payload = verify_token(token)
    if not payload:
        return None
    
    return payload.get("sub")

@app.get("/", response_class=HTMLResponse)
async def check_in_form(request: Request):
    return templates.TemplateResponse("check_in.html", {
        "request": request,
        "visitor_token": request.cookies.get("visitor_token")
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    correct_username = os.getenv("ADMIN_USERNAME")
    correct_password = os.getenv("ADMIN_PASSWORD")
    
    if username != correct_username or password != correct_password:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Invalid credentials"}
        )
    
    access_token = create_access_token({"sub": username, "role": "admin"})
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(
        key="admin_token",
        value=access_token,
        httponly=True,
        max_age=86400,
        secure=os.getenv("ENVIRONMENT", "development") == "production"
    )
    return response

async def get_current_admin(request: Request):
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=303, detail="Not authenticated")
    
    payload = verify_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=303, detail="Not authenticated")
    
    return payload.get("sub")

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(database.get_db),
    admin: str = Depends(get_current_admin)
):
    try:
        visitors = db.query(models.Visitor).all()
        return templates.TemplateResponse(
            "admin.html",
            {"request": request, "visitors": visitors, "admin": True}
        )
    except HTTPException:
        return RedirectResponse(url="/login", status_code=303)

@app.post("/check-in")
async def check_in(
    request: Request,
    name: str = Form(...),
    host_name: str = Form(...),
    reason: str = Form(...),
    db: Session = Depends(database.get_db)
):
    visitor = models.Visitor(
        name=name,
        host_name=host_name,
        reason=reason
    )
    db.add(visitor)
    db.commit()
    db.refresh(visitor)
    
    access_token = create_access_token({"sub": str(visitor.id)})
    response = RedirectResponse(url=f"/status/{visitor.id}", status_code=303)
    response.set_cookie(
        key="visitor_token",
        value=access_token,
        httponly=True,
        max_age=86400,
        secure=os.getenv("ENVIRONMENT", "development") == "production"
    )
    return response

@app.get("/status/{visitor_id}", response_class=HTMLResponse)
async def visitor_status(
    request: Request,
    visitor_id: int,
    db: Session = Depends(database.get_db),
    current_visitor: str = Depends(get_current_visitor)
):
    if not current_visitor or current_visitor != str(visitor_id):
        return RedirectResponse(url="/", status_code=303)
        
    visitor = db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    return templates.TemplateResponse("visitor_status.html", {
        "request": request,
        "visitor": visitor,
        "visitor_token": request.cookies.get("visitor_token")
    })

@app.post("/check-out/{visitor_id}")
async def check_out(
    visitor_id: int,
    request: Request,
    db: Session = Depends(database.get_db),
    current_visitor: str = Depends(get_current_visitor)
):
    if not current_visitor or current_visitor != str(visitor_id):
        raise HTTPException(status_code=403, detail="Not authorized")
        
    visitor = db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    visitor.check_out_time = datetime.now()
    visitor.is_checked_out = True
    db.commit()
    
    response = {"message": "Checked out successfully"}
    return response

@app.post("/admin-checkout/{visitor_id}")
async def admin_checkout(
    visitor_id: int,
    db: Session = Depends(database.get_db),
    admin: str = Depends(get_current_admin)
):
    visitor = db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    visitor.check_out_time = datetime.now()
    visitor.is_checked_out = True
    db.commit()
    
    return {"success": True, "message": "Visitor checked out successfully"}

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(database.get_db),
    admin: str = Depends(get_current_admin)
):
    visitors = db.query(models.Visitor).all()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request, 
            "visitors": visitors,
            "admin": True,
            "visitor_token": request.cookies.get("visitor_token")
        }
    )

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("visitor_token")
    response.delete_cookie("admin_token")
    return response

# Error handlers
@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/", status_code=303)

@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/", status_code=303)
