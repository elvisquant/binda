#HERE WE USE FASTAPI WITH SQLALCHEMY :USING ORM
import os
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from . import models 
from .database import engine
from .routers import  dashboard_data_api,analytics_api,user, auth,category_document,vehicle_make,vehicle_model,vehicle_type,vehicle_transmission,category_maintenance,category_panne,document_vehicle,driver,vehicle,fuel,garage,panne,reparation,trip,fuel_type
from .config import settings
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
models.Base.metadata.create_all(bind = engine)


try:
    print("Attempting to create database tables if they don't exist...")
    models.Base.metadata.create_all(bind=engine)
    print("Database tables checked/created successfully.")
except Exception as e:
    print(f"CRITICAL ERROR during table creation: {e}")

# --- Import Your API Router for Authentication ---
try:
    # For your API endpoint: POST /login/
    from .routers import  dashboard_data_api,analytics_api,user, auth,category_document,vehicle_make,vehicle_model,vehicle_type,vehicle_transmission,category_maintenance,category_panne,document_vehicle,driver,vehicle,fuel,garage,panne,reparation,trip,fuel_type,fuel,maintenance

except ImportError as e:
    print(f"CRITICAL ERROR: Could not import router from app.routers.auth: {e}.")
    print("Ensure 'app/routers/auth.py' exists in the 'app/routers/' package,")
    print("and defines 'router = APIRouter(...)'.")
    raise

# Create the FastAPI application instance
app = FastAPI(
    title="FleetDash Application",
    description="Main application providing API and Frontend for fleet management.",
    version="1.0.3", # Updated version example
)

# --- Define Base Directory and Paths ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))  # 'your_project/app'
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")    # 'your_project/app/templates'
STATIC_DIR = os.path.join(APP_DIR, "static")          # 'your_project/app/static'

print(f"--- Application Paths (app/main.py) ---")
print(f"APP_DIR (location of main.py): {APP_DIR}")
print(f"TEMPLATES_DIR (for Jinja2): {TEMPLATES_DIR}")
print(f"STATIC_DIR (for CSS/JS): {STATIC_DIR}")

# --- Setup Jinja2 Templating ---
if not os.path.isdir(TEMPLATES_DIR):
    print(f"CRITICAL ERROR: Templates directory NOT FOUND at: {TEMPLATES_DIR}")
    templates = None # To prevent NameError if routes are called before this check fully stops app
else:
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    print(f"Jinja2 templates initialized from: {TEMPLATES_DIR}")

# --- Mount Static Files (from app/static/) ---
if not os.path.isdir(STATIC_DIR):
    print(f"WARNING: Static files directory NOT FOUND at: {STATIC_DIR}. /static paths will not work.")
else:
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"Mounted static files from {STATIC_DIR} at /static")

# --- Include Your Authentication API Router FIRST ---
# This ensures its specific path (POST /login/) takes precedence.
app.include_router(auth.router)

# If you have other DATA API routers (e.g., for /api/trips, /api/vehicles), include them here.
# Example:
# from .routers import trip_api # Assuming you create app/routers/trip_api.py
# app.include_router(trip_api.router, prefix="/api/trips", tags=["Trip Data API"])
# Include your routers
#app.include_router(auth.router)  
app.include_router(user.router)
app.include_router(category_document.router)
app.include_router(category_maintenance.router)
app.include_router(maintenance.router)
app.include_router(category_panne.router)
app.include_router(document_vehicle.router)
app.include_router(driver.router)
app.include_router(fuel.router)
app.include_router(garage.router)
app.include_router(panne.router)
app.include_router(reparation.router)
app.include_router(trip.router)
app.include_router(fuel_type.router)
app.include_router(vehicle.router)
app.include_router(vehicle_make.router)
app.include_router(vehicle_model.router)
app.include_router(vehicle_transmission.router)
app.include_router(vehicle_type.router)
app.include_router(dashboard_data_api.router)
app.include_router(analytics_api.router)

# --- Helper function to serve Jinja2 templates from app/templates ---
async def serve_html_template(template_name: str, request: Request, context: dict = None):
    """DRY helper to render and return an HTML template."""
    if templates is None: # Check if templates object was initialized
        raise HTTPException(status_code=500, detail="Server configuration error: Templates not initialized.")
    
    full_template_path = os.path.join(TEMPLATES_DIR, template_name)
    if not os.path.exists(full_template_path):
        print(f"ERROR: Template file '{template_name}' not found at {full_template_path}")
        raise HTTPException(status_code=404, detail=f"Page template '{template_name}' could not be found.")
    
    if context is None:
        context = {}
    context.update({"request": request}) # Always include request in context for url_for etc.
    
    print(f"Serving template '{template_name}' for request path: {request.url.path}")
    return templates.TemplateResponse(template_name, context)

# --- HTML Page Serving Routes (All handled in main.py) ---

# --- General User Frontend Pages ---
@app.get("/", response_class=HTMLResponse, name="root_login_page", tags=["Frontend Pages"])
async def serve_root_as_login(request: Request):
    """Serves login.html from app/templates/ for the root domain path."""
    return await serve_html_template("login.html", request)

@app.get("/login", response_class=HTMLResponse, name="explicit_login_page", tags=["Frontend Pages"])
async def serve_login_page_explicitly(request: Request):
    """Serves login.html from app/templates/ for the /login path (GET request)."""
    return await serve_html_template("login.html", request)

@app.get("/dashboard", response_class=HTMLResponse, name="dashboard_page", tags=["Frontend Pages"])
async def serve_dashboard_page(request: Request):
    """Serves dashboard.html from app/templates/."""
    return await serve_html_template("dashboard.html", request)

@app.get("/trip", response_class=HTMLResponse, name="trip_page", tags=["Frontend Pages"])
async def serve_trip_page(request: Request):
    """Serves trip.html from app/templates/."""
    return await serve_html_template("trip.html", request)

@app.get("/analytics", response_class=HTMLResponse, name="analytics_page", tags=["Frontend Pages"])
async def serve_analytics_page(request: Request):
    """Serves analytics.html from app/templates/."""
    return await serve_html_template("analytics.html", request)

@app.get("/users", response_class=HTMLResponse, name="users_page", tags=["Frontend Pages"])
async def serve_users_page(request: Request):
    """Serves users.html from app/templates/ (e.g., for user profile or general user list)."""
    return await serve_html_template("users.html", request)

@app.get("/driver", response_class=HTMLResponse, name="driver_page", tags=["Frontend Pages"])
async def serve_driver_page(request: Request):
    """Serves driver.html from app/templates/."""
    return await serve_html_template("driver.html", request)

@app.get("/vehicle", response_class=HTMLResponse, name="vehicle_page", tags=["Frontend Pages"])
async def serve_vehicle_page(request: Request):
    """Serves vehicle.html from app/templates/."""
    return await serve_html_template("vehicle.html", request)

@app.get("/maintenance", response_class=HTMLResponse, name="maintenance_page", tags=["Frontend Pages"])
async def serve_maintenance_page(request: Request):
    """Serves maintenance.html from app/templates/."""
    return await serve_html_template("maintenance.html", request)

@app.get("/reparation", response_class=HTMLResponse, name="reparation_page", tags=["Frontend Pages"])
async def serve_reparation_page(request: Request):
    """Serves reparation.html from app/templates/."""
    return await serve_html_template("reparation.html", request)

@app.get("/panne", response_class=HTMLResponse, name="panne_page", tags=["Frontend Pages"])
async def serve_panne_page(request: Request):
    """Serves panne.html from app/templates/."""
    return await serve_html_template("panne.html", request)

@app.get("/fuel", response_class=HTMLResponse, name="fuel_page", tags=["Frontend Pages"])
async def serve_fuel_page(request: Request):
    """Serves fuel.html from app/templates/."""
    return await serve_html_template("fuel.html", request)



















































                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        