# app/routers/admin_views.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Assuming templates are in app/templates
templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/admin" ,
    tags=["Admin Views"],
    # prefix="/admin" # Optional: if you want all routes here to start with /admin
)

@router.get("/loginpage", response_class=HTMLResponse, name="login_page_html")
async def get_login_page(request: Request):
    # Check if user is already logged in (e.g., via a cookie or by trying to get current_user)
    # For simplicity, just serving the page. A more robust check could be added.
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/admin", response_class=HTMLResponse, name="admin_dashboard_html")
async def get_admin_dashboard(request: Request):
    # This route serves the admin.html page.
    # The actual check for a valid token in localStorage happens client-side in admin.html's JS.
    # If you wanted server-side protection for this HTML page itself (e.g., if it contained
    # sensitive data rendered directly by Jinja), you would add Depends(oauth2.get_current_user) here.
    # However, for SPAs or client-heavy pages, client-side check is common.
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Example of a server-side protected HTML page (alternative to client-side check)
# from .. import oauth2, models
# @router.get("/admin-protected", response_class=HTMLResponse)
# async def get_admin_dashboard_protected(request: Request, current_user: models.User = Depends(oauth2.get_current_user)):
#     return templates.TemplateResponse("admin.html", {"request": request, "user": current_user})


@router.get("/analytics", response_class=HTMLResponse, name="analytics_page_html")
async def get_page(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

@router.get("/analytics", response_class=HTMLResponse, name="analytics_page_html")
async def get_page(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

@router.get("/users", response_class=HTMLResponse, name="user_page_html")
async def get_page(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})

@router.get("/driver", response_class=HTMLResponse, name="driver_page_html")
async def get_page(request: Request):
    return templates.TemplateResponse("driver.html", {"request": request})


@router.get("/vehicle", response_class=HTMLResponse, name="vehicle_page_html")
async def get_page(request: Request):
    return templates.TemplateResponse("vehicle.html", {"request": request})

@router.get("/maintenance", response_class=HTMLResponse, name="maintenance_page_html")
async def get_page(request: Request):
    return templates.TemplateResponse("maintenance.html", {"request": request})



@router.get("/reparation", response_class=HTMLResponse, name="reparation_page_html")
async def get_page(request: Request):
    return templates.TemplateResponse("reparation.html", {"request": request})



@router.get("/panne", response_class=HTMLResponse, name="panne_page_html")
async def get_page(request: Request):
    return templates.TemplateResponse("panne.html", {"request": request})



@router.get("/fuel", response_class=HTMLResponse, name="fuel_page_html")
async def get_page(request: Request):
    return templates.TemplateResponse("fuel.html", {"request": request})


@router.get("/trip", response_class=HTMLResponse, name="trip_page_html")
async def get_page(request: Request):
    return templates.TemplateResponse("trip.html", {"request": request})

