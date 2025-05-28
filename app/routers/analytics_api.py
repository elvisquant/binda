from fastapi import APIRouter, Depends, Query # Removed HTTPException, status, selectinload, or_ unless used elsewhere in this file
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract, and_ # 'and_' might be useful if combining filters
from typing import List, Optional
from datetime import datetime, date # Correctly aliasing 'date' from 'datetime'
from pydantic import BaseModel
from calendar import month_abbr

# Adjust these imports to match your project structure
from .. import models, schemas, oauth2 
from ..database import get_db


# THIS WAS MISSING/IMPLIED in previous snippets for this specific file:
router = APIRouter(
    prefix="/analytics-data",
    tags=["Analytics Data (Expenses & Performance)"],
    dependencies=[Depends(oauth2.get_current_user)]
)



# Helper function
def get_month_year_str(year: int, month: int) -> str:
    return f"{month_abbr[month]} '{str(year)[-2:]}"

# --- API Endpoints ---

@router.get("/expense-summary", response_model=schemas.AnalyticsExpenseSummaryResponse)
async def get_expense_summary_data(
    start_date: date, # Parameter type is date
    end_date: date,   # Parameter type is date
    db: Session = Depends(get_db)
):
    end_datetime = datetime.combine(end_date, datetime.max.time())
    start_datetime = datetime.combine(start_date, datetime.min.time())

    # --- 1. Calculate Total Costs ---
    total_fuel_cost = db.query(func.sum(models.Fuel.cost)).filter(
        models.Fuel.created_at >= start_datetime, # Fuel.created_at is likely DATETIME
        models.Fuel.created_at <= end_datetime
    ).scalar() or 0.0

    total_reparation_cost = db.query(func.sum(models.Reparation.cost)).filter(
        # Assuming Reparation.repair_date is DATE in DB
        models.Reparation.repair_date >= start_date,
        models.Reparation.repair_date <= end_date
        # If Reparation.repair_date is DATETIME in DB, use:
        # models.Reparation.repair_date >= start_datetime,
        # models.Reparation.repair_date <= end_datetime
    ).scalar() or 0.0

    total_maintenance_cost = db.query(func.sum(models.Maintenance.cost)).filter(
        # Assuming Maintenance.maintenance_date is DATE in DB
        models.Maintenance.maintenance_date >= start_date,
        models.Maintenance.maintenance_date <= end_date
    ).scalar() or 0.0

    total_vehicle_purchase_cost = db.query(func.sum(models.Vehicle.purchase_price)).filter(
        # Assuming Vehicle.purchase_date is DATE in DB
        models.Vehicle.purchase_date >= start_date,
        models.Vehicle.purchase_date <= end_date
    ).scalar() or 0.0

    # --- 2. Calculate Monthly Breakdown ---
    monthly_data_temp = {}

    # Fuel by month
    fuel_monthly_q = db.query(
        extract('year', models.Fuel.created_at).label('year'),
        extract('month', models.Fuel.created_at).label('month'),
        func.sum(models.Fuel.cost).label('total_cost')
    ).filter(
        models.Fuel.created_at >= start_datetime,
        models.Fuel.created_at <= end_datetime
    ).group_by('year', 'month').all()
    for row in fuel_monthly_q:
        key = f"{int(row.year)}-{int(row.month):02d}"
        if key not in monthly_data_temp: monthly_data_temp[key] = {}
        monthly_data_temp[key]['fuel_cost'] = (monthly_data_temp[key].get('fuel_cost', 0) + row.total_cost) if row.total_cost else monthly_data_temp[key].get('fuel_cost', 0)

    # Reparations by month
    reparations_monthly_q = db.query(
        extract('year', models.Reparation.repair_date).label('year'),
        extract('month', models.Reparation.repair_date).label('month'),
        func.sum(models.Reparation.cost).label('total_cost')
    ).filter(
        models.Reparation.repair_date >= start_date, # Adjust if DATETIME
        models.Reparation.repair_date <= end_date    # Adjust if DATETIME
    ).group_by('year', 'month').all()
    for row in reparations_monthly_q:
        key = f"{int(row.year)}-{int(row.month):02d}"
        if key not in monthly_data_temp: monthly_data_temp[key] = {}
        monthly_data_temp[key]['reparation_cost'] = (monthly_data_temp[key].get('reparation_cost', 0) + row.total_cost) if row.total_cost else monthly_data_temp[key].get('reparation_cost', 0)

    # Maintenance by month
    maintenance_monthly_q = db.query(
        extract('year', models.Maintenance.maintenance_date).label('year'),
        extract('month', models.Maintenance.maintenance_date).label('month'),
        func.sum(models.Maintenance.cost).label('total_cost')
    ).filter(
        models.Maintenance.maintenance_date >= start_date, # Adjust if DATETIME
        models.Maintenance.maintenance_date <= end_date    # Adjust if DATETIME
    ).group_by('year', 'month').all()
    for row in maintenance_monthly_q:
        key = f"{int(row.year)}-{int(row.month):02d}"
        if key not in monthly_data_temp: monthly_data_temp[key] = {}
        monthly_data_temp[key]['maintenance_cost'] = (monthly_data_temp[key].get('maintenance_cost', 0) + row.total_cost) if row.total_cost else monthly_data_temp[key].get('maintenance_cost', 0)
    
    # Vehicle Purchases by month
    purchases_monthly_q = db.query(
        extract('year', models.Vehicle.purchase_date).label('year'),
        extract('month', models.Vehicle.purchase_date).label('month'),
        func.sum(models.Vehicle.purchase_price).label('total_cost')
    ).filter(
        models.Vehicle.purchase_date >= start_date, # Adjust if DATETIME
        models.Vehicle.purchase_date <= end_date,   # Adjust if DATETIME
        models.Vehicle.purchase_price > 0 # Only actual purchases
    ).group_by('year', 'month').all()
    for row in purchases_monthly_q:
        key = f"{int(row.year)}-{int(row.month):02d}"
        if key not in monthly_data_temp: monthly_data_temp[key] = {}
        monthly_data_temp[key]['purchase_cost'] = (monthly_data_temp[key].get('purchase_cost', 0) + row.total_cost) if row.total_cost else monthly_data_temp[key].get('purchase_cost', 0)

    # --- 3. Format monthly_breakdown ---
    final_monthly_breakdown: List[schemas.MonthlyExpenseItem] = []
    current_iter_date = start_date
    while current_iter_date <= end_date:
        year, month = current_iter_date.year, current_iter_date.month
        month_year_key = f"{year}-{month:02d}"
        month_year_display_str = get_month_year_str(year, month)
        data_for_month = monthly_data_temp.get(month_year_key, {})
        final_monthly_breakdown.append(schemas.MonthlyExpenseItem(
            month_year=month_year_display_str,
            fuel_cost=data_for_month.get('fuel_cost', 0.0),
            reparation_cost=data_for_month.get('reparation_cost', 0.0),
            maintenance_cost=data_for_month.get('maintenance_cost', 0.0),
            purchase_cost=data_for_month.get('purchase_cost', 0.0)
        ))
        if month == 12:
            current_iter_date = date(year + 1, 1, 1)
        else:
            current_iter_date = date(year, month + 1, 1)
            
    return schemas.AnalyticsExpenseSummaryResponse(
        total_fuel_cost=total_fuel_cost,
        total_reparation_cost=total_reparation_cost,
        total_maintenance_cost=total_maintenance_cost,
        total_vehicle_purchase_cost=total_vehicle_purchase_cost,
        monthly_breakdown=final_monthly_breakdown
    )


@router.get("/detailed-expense-records", response_model=schemas.DetailedReportDataResponse)
async def get_detailed_expense_records(
    start_date: date, # Parameter type is date
    end_date: date,   # Parameter type is date
    categories: List[str] = Query(None, description="List of categories: fuel, reparation, maintenance, purchases"),
    db: Session = Depends(get_db)
):
    response_data = schemas.DetailedReportDataResponse()
    end_datetime = datetime.combine(end_date, datetime.max.time())
    start_datetime = datetime.combine(start_date, datetime.min.time())

    if not categories:
        categories = ["fuel", "reparation", "maintenance", "purchases"]

    if "fuel" in categories:
        fuel_q = db.query(models.Fuel).options(
            joinedload(models.Fuel.vehicle)
        ).filter(
            models.Fuel.created_at >= start_datetime,
            models.Fuel.created_at <= end_datetime
        ).order_by(models.Fuel.created_at.asc()).all()
        
        response_data.fuel_records = [
            schemas.FuelRecordDetail.from_orm(f) for f in fuel_q # Simplified with from_orm
            # If you need custom mapping (e.g. vehicle_plate):
            # FuelRecordDetail(
            #     id=f.id,
            #     vehicle_plate=f.vehicle.plate_number if f.vehicle else "N/A",
            #     date=f.created_at,
            #     quantity=f.quantity,
            #     cost=f.cost,
            #     notes=f.notes
            # ) for f in fuel_q
        ]

    if "reparation" in categories:
        reparation_q = db.query(models.Reparation).options(
            joinedload(models.Reparation.vehicle)
        ).filter(
            models.Reparation.repair_date >= start_date, # Adjust if DATETIME
            models.Reparation.repair_date <= end_date    # Adjust if DATETIME
        ).order_by(models.Reparation.repair_date.asc()).all()
        
        response_data.reparation_records = [
            schemas.ReparationRecordDetail.from_orm(r) for r in reparation_q # Simplified
            # Or custom mapping:
            # ReparationRecordDetail(
            #     id=r.id,
            #     vehicle_plate=r.vehicle.plate_number if r.vehicle else "N/A",
            #     repair_date=r.repair_date,
            #     description=r.description,
            #     cost=r.cost,
            #     provider=r.provider
            # ) for r in reparation_q
        ]

    if "maintenance" in categories:
        maintenance_q = db.query(models.Maintenance).options(
            joinedload(models.Maintenance.vehicle),
            joinedload(models.Maintenance.category_maintenance)
        ).filter(
            models.Maintenance.maintenance_date >= start_date, # Adjust if DATETIME
            models.Maintenance.maintenance_date <= end_date    # Adjust if DATETIME
        ).order_by(models.Maintenance.maintenance_date.asc()).all()

        response_data.maintenance_records = [
            # MaintenanceRecordDetail.from_orm(m) for m in maintenance_q # Simplified
            # Custom mapping needed for category_maintenance.cat_maintenance
            schemas.MaintenanceRecordDetail(
                id=m.id,
                vehicle_plate=m.vehicle.plate_number if m.vehicle else "N/A",
                maintenance_date=m.maintenance_date,
                description=m.category_maintenance.cat_maintenance if m.category_maintenance and hasattr(m.category_maintenance, 'cat_maintenance') else (m.description or "N/A"),
                cost=m.cost,
                provider=m.provider
            ) for m in maintenance_q
        ]

    if "purchases" in categories:
        purchase_q = db.query(models.Vehicle).options(
            joinedload(models.Vehicle.make_ref),
            joinedload(models.Vehicle.model_ref)
        ).filter(
            models.Vehicle.purchase_date >= start_date, # Adjust if DATETIME
            models.Vehicle.purchase_date <= end_date,   # Adjust if DATETIME
            models.Vehicle.purchase_price > 0
        ).order_by(models.Vehicle.purchase_date.asc()).all()

        response_data.purchase_records = [
            # PurchaseRecordDetail.from_orm(v) for v in purchase_q # Simplified
            # Custom mapping for make/model names
            schemas.PurchaseRecordDetail(
                id=v.id,
                plate_number=v.plate_number,
                make=v.make_ref.vehicle_make if v.make_ref and hasattr(v.make_ref, 'vehicle_make') else "N/A",
                model=v.model_ref.vehicle_model if v.model_ref and hasattr(v.model_ref, 'vehicle_model') else "N/A",
                purchase_date=v.purchase_date,
                purchase_price=v.purchase_price
            ) for v in purchase_q
        ]
        
    return response_data