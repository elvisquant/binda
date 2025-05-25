# backend_app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

# --- Your existing imports ---
from .routers import auth as auth_router # Make sure this import is correct
# from .routers import user as user_router, panne as panne_router # Example
# ... other imports for your API routers ...

app = FastAPI(
    title="FleetDash API",
    description="API for managing fleet operations.",
    version="1.0.0"
)

# --- Include your API Routers FIRST ---
# This is important so they take precedence for their specific paths.
app.include_router(auth_router.router) # This makes POST /login/ available
# app.include_router(user_router.router, prefix="/users", tags=["Users"])
# app.include_router(panne_router.router, prefix="/panne", tags=["Pannes"])
# ... include all your other API routers ...


# --- Define Path to Frontend Directory ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "fleet-management")

if not os.path.isdir(FRONTEND_DIR):
    print(f"ERROR: Frontend directory not found at: {FRONTEND_DIR}")
    # Consider raising an error or exiting

# --- Mount Static File Directories (CSS, JS, etc.) ---
if os.path.isdir(os.path.join(FRONTEND_DIR, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
# ... mount /js, /content, /assets ...


# --- Serve HTML Files (These should generally come AFTER API routers) ---

# Route to serve the login.html page
@app.get("/login", response_class=HTMLResponse, tags=["Frontend Pages"])
async def get_login_page(): # Changed function name for clarity
    login_html_path = os.path.join(FRONTEND_DIR, "login.html")
    if not os.path.exists(login_html_path):
        raise HTTPException(status_code=404, detail="login.html not found")
    with open(login_html_path, "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# Route to serve the dashboard.html page
@app.get("/dashboard", response_class=HTMLResponse, tags=["Frontend Pages"])
async def get_dashboard_page(): # Changed function name for clarity
    dashboard_html_path = os.path.join(FRONTEND_DIR, "dashboard.html")
    if not os.path.exists(dashboard_html_path):
        raise HTTPException(status_code=404, detail="dashboard.html not found")
    with open(dashboard_html_path, "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# Optional: Serve login.html as the default page for "/"
@app.get("/", response_class=HTMLResponse, tags=["Frontend Pages"])
async def get_root_page_as_login():
    login_html_path = os.path.join(FRONTEND_DIR, "login.html")
    if not os.path.exists(login_html_path):
        raise HTTPException(status_code=404, detail="login.html not found")
    with open(login_html_path, "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# --- SPA Fallback (if needed for /dashboard/* non-hash routes, not strictly for /dashboard#hash) ---
# If you use path-based routing on client like /dashboard/pannes (NO hash), you need this.
# For hash-based routing (/dashboard#pannes), the @app.get("/dashboard") is enough.
# To keep it simple, let's assume you only need the explicit /dashboard route for now.
# If you need a broader SPA fallback, it must be the *very last* GET route.
# @app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
# async def serve_spa_host(full_path: str):
#     # This is a simplified SPA fallback. It assumes any other path should serve dashboard.html.
#     # In a real app, you might want to check if the user is authenticated before serving dashboard.html
#     # or always serve it and let client-side JS handle auth redirects.
#     dashboard_html_path = os.path.join(FRONTEND_DIR, "dashboard.html")
#     if not os.path.exists(dashboard_html_path):
#         raise HTTPException(status_code=404, detail="Application host page (dashboard.html) not found")
#     with open(dashboard_html_path, "r") as f:
#         return HTMLResponse(content=f.read(), status_code=200)

































































































                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        