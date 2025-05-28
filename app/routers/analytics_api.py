from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract, and_
from typing import List, Optional
from datetime import datetime, date as DateType # Aliased to avoid conflict
from pydantic import BaseModel
from calendar import month_abbr

# Adjust these imports to match your project structure
from .. import models, schemas, oauth2 
from ..database import get_db

router = APIRouter(
    prefix="/analytics-data",
    tags=["Analytics Data (Expenses & Performance)"],
    dependencies=[Depends(oauth2.get_current_user)]
)

# Helper function
def get_month_year_str(year: int, month: int) -> str:
    return f"{month_abbr[month]} '{str(year)[-2:]}"
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract, text # Removed 'and_' as it wasn't used directly
from typing import List, Optional
from datetime import datetime, date as DateType 
from calendar import month_abbr

from .. import models, schemas, oauth2 
from ..database import get_db

router = APIRouter(
    prefix="/analytics-data",
    tags=["Analytics Data (Expenses & Performance)"],
    dependencies=[Depends(oauth2.get_current_user)]
)

# Helper function
def get_month_year_str(year: int, month: int) -> str:
    return f"{month_abbr[month]} '{str(year)[-2:]}"

@router.get("/expense-summary", response_model=schemas.AnalyticsExpenseSummaryResponse)
async def get_expense_summary_data(
    start_date: DateType, 
    end_date: DateType,   
    db: Session = Depends(get_db)
):
    # Convert query date parameters to datetime for full day coverage in filters
    # This is crucial for TIMESTAMP columns in the database.
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    # --- 1. Calculate Total Costs ---
    # Assuming models.Fuel.created_at is DATETIME
    total_fuel_cost = db.query(func.sum(models.Fuel.cost)).filter(
        models.Fuel.created_at >= start_datetime,
        models.Fuel.created_at <= end_datetime
    ).scalar() or 0.0

    # Assuming models.Reparation.repair_date is DATETIME
    total_reparation_cost = db.query(func.sum(models.Reparation.cost)).filter(
        models.Reparation.repair_date >= start_datetime,
        models.Reparation.repair_date <= end_datetime
    ).scalar() or 0.0

    # Corrected to use models.Maintenance.maintenance_cost
    # Assuming models.Maintenance.maintenance_date is DATETIME
    total_maintenance_cost = db.query(func.sum(models.Maintenance.maintenance_cost)).filter(
        models.Maintenance.maintenance_date >= start_datetime,
        models.Maintenance.maintenance_date <= end_datetime
    ).scalar() or 0.0

    # Assuming models.Vehicle.purchase_date is DATETIME
    total_vehicle_purchase_cost = db.query(func.sum(models.Vehicle.purchase_price)).filter(
        models.Vehicle.purchase_date >= start_datetime,
        models.Vehicle.purchase_date <= end_datetime,
        models.Vehicle.purchase_price.isnot(None) 
    ).scalar() or 0.0

    # --- 2. Calculate Monthly Breakdown ---
    monthly_data_temp = {}

    # Fuel by month
    year_col_fuel = extract('year', models.Fuel.created_at)
    month_col_fuel = extract('month', models.Fuel.created_at)
    fuel_monthly_q = db.query(
        year_col_fuel.label('year'),
        month_col_fuel.label('month'),
        func.sum(models.Fuel.cost).label('total_cost')
    ).filter(
        models.Fuel.created_at >= start_datetime,
        models.Fuel.created_at <= end_datetime
    ).group_by(year_col_fuel, month_col_fuel).all()
    for row in fuel_monthly_q:
        key = f"{int(row.year)}-{int(row.month):02d}"
        if key not in monthly_data_temp: monthly_data_temp[key] = {}
        monthly_data_temp[key]['fuel_cost'] = (monthly_data_temp[key].get('fuel_cost', 0) + row.total_cost) if row.total_cost else monthly_data_temp[key].get('fuel_cost', 0)

    # Reparations by month
    year_col_rep = extract('year', models.Reparation.repair_date)
    month_col_rep = extract('month', models.Reparation.repair_date)
    reparations_monthly_q = db.query(
        year_col_rep.label('year'),
        month_col_rep.label('month'),
        func.sum(models.Reparation.cost).label('total_cost')
    ).filter(
        models.Reparation.repair_date >= start_datetime, 
        models.Reparation.repair_date <= end_datetime    
    ).group_by(year_col_rep, month_col_rep).all()
    for row in reparations_monthly_q:
        key = f"{int(row.year)}-{int(row.month):02d}"
        if key not in monthly_data_temp: monthly_data_temp[key] = {}
        monthly_data_temp[key]['reparation_cost'] = (monthly_data_temp[key].get('reparation_cost', 0) + row.total_cost) if row.total_cost else monthly_data_temp[key].get('reparation_cost', 0)

    # Maintenance by month (Corrected to maintenance_cost and explicit group by)
    year_col_maint = extract('year', models.Maintenance.maintenance_date)
    month_col_maint = extract('month', models.Maintenance.maintenance_date)
    maintenance_monthly_q = db.query(
        year_col_maint.label('year'),
        month_col_maint.label('month'),
        func.sum(models.Maintenance.maintenance_cost).label('total_cost') 
    ).filter(
        models.Maintenance.maintenance_date >= start_datetime, 
        models.Maintenance.maintenance_date <= end_datetime    
    ).group_by(year_col_maint, month_col_maint).all()
    for row in maintenance_monthly_q:
        key = f"{int(row.year)}-{int(row.month):02d}"
        if key not in monthly_data_temp: monthly_data_temp[key] = {}
        monthly_data_temp[key]['maintenance_cost'] = (monthly_data_temp[key].get('maintenance_cost', 0) + row.total_cost) if row.total_cost else monthly_data_temp[key].get('maintenance_cost', 0)
    
    # Vehicle Purchases by month (Corrected with explicit group by)
    year_col_vehicle_purchase = extract('year', models.Vehicle.purchase_date)
    month_col_vehicle_purchase = extract('month', models.Vehicle.purchase_date)
    purchases_monthly_q = db.query(
        year_col_vehicle_purchase.label('year'),
        month_col_vehicle_purchase.label('month'),
        func.sum(models.Vehicle.purchase_price).label('total_cost')
    ).filter(
        models.Vehicle.purchase_date >= start_datetime, 
        models.Vehicle.purchase_date <= end_datetime,   
        models.Vehicle.purchase_price > 0 
    ).group_by(
        year_col_vehicle_purchase,
        month_col_vehicle_purchase
    ).all()
    for row in purchases_monthly_q:
        key = f"{int(row.year)}-{int(row.month):02d}"
        if key not in monthly_data_temp: monthly_data_temp[key] = {}
        monthly_data_temp[key]['purchase_cost'] = (monthly_data_temp[key].get('purchase_cost', 0) + row.total_cost) if row.total_cost else monthly_data_temp[key].get('purchase_cost', 0)

    # --- 3. Format monthly_breakdown ---
    final_monthly_breakdown: List[schemas.MonthlyExpenseItem] = []
    # Iterate from the first day of the start_date's month to the first day of the end_date's month
    current_iter_date_month_start = DateType(start_date.year, start_date.month, 1)
    loop_end_date_month_start = DateType(end_date.year, end_date.month, 1)

    while current_iter_date_month_start <= loop_end_date_month_start:
        year, month = current_iter_date_month_start.year, current_iter_date_month_start.month
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
            current_iter_date_month_start = DateType(year + 1, 1, 1)
        else:
            current_iter_date_month_start = DateType(year, month + 1, 1)
            
    return schemas.AnalyticsExpenseSummaryResponse(
        total_fuel_cost=total_fuel_cost,
        total_reparation_cost=total_reparation_cost,
        total_maintenance_cost=total_maintenance_cost,
        total_vehicle_purchase_cost=total_vehicle_purchase_cost,
        monthly_breakdown=final_monthly_breakdown
    )


@router.get("/detailed-expense-records", response_model=schemas.DetailedReportDataResponse)
async def get_detailed_expense_records(
    start_date: DateType, 
    end_date: DateType,   
    categories: List[str] = Query(None, description="List of categories: fuel, reparation, maintenance, purchases"),
    db: Session = Depends(get_db)
):
    response_data = schemas.DetailedReportDataResponse()
    # Convert query date parameters to datetime for full day coverage in filters
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    if not categories: # If no categories specified, include all
        categories = ["fuel", "reparation", "maintenance", "purchases"]

    if "fuel" in categories:
        # Assuming models.Fuel.created_at is DATETIME
        fuel_q = db.query(models.Fuel).options(
            joinedload(models.Fuel.vehicle)
        ).filter(
            models.Fuel.created_at >= start_datetime,
            models.Fuel.created_at <= end_datetime
        ).order_by(models.Fuel.created_at.asc()).all()
        
        response_data.fuel_records = [
            schemas.FuelRecordDetail(
                id=f.id,
                vehicle_plate=f.vehicle.plate_number if f.vehicle and hasattr(f.vehicle, 'plate_number') else "N/A",
                date=f.created_at,
                quantity=f.quantity,
                cost=f.cost,
                notes=f.notes
            ) for f in fuel_q
        ]

    if "reparation" in categories:
        # Assuming models.Reparation.repair_date is DATETIME
        reparation_q = db.query(models.Reparation).options(
            joinedload(models.Reparation.vehicle),
            joinedload(models.Reparation.panne) # If you need panne description for reparation
        ).filter(
            models.Reparation.repair_date >= start_datetime,
            models.Reparation.repair_date <= end_datetime
        ).order_by(models.Reparation.repair_date.asc()).all()
        
        response_data.reparation_records = [
            schemas.ReparationRecordDetail(
                id=r.id,
                vehicle_plate=r.vehicle.plate_number if r.vehicle and hasattr(r.vehicle, 'plate_number') else "N/A",
                repair_date=r.repair_date.date(), # Convert datetime to date for schema
                description=r.panne.description if r.panne and hasattr(r.panne, 'description') else "N/A", # Example if description comes from Panne
                cost=r.cost,
                provider=r.garage.nom_garage if r.garage and hasattr(r.garage, 'nom_garage') else (r.provider if hasattr(r, 'provider') else None) # Example using garage name as provider
            ) for r in reparation_q
        ]

    if "maintenance" in categories:
        # Assuming models.Maintenance.maintenance_date is DATETIME
        maintenance_q = db.query(models.Maintenance).options(
            joinedload(models.Maintenance.vehicle),
            joinedload(models.Maintenance.category_maintenance),
            joinedload(models.Maintenance.garage)
        ).filter(
            models.Maintenance.maintenance_date >= start_datetime,
            models.Maintenance.maintenance_date <= end_datetime
        ).order_by(models.Maintenance.maintenance_date.asc()).all()

        response_data.maintenance_records = [
            schemas.MaintenanceRecordDetail(
                id=m.id,
                vehicle_plate=m.vehicle.plate_number if m.vehicle and hasattr(m.vehicle, 'plate_number') else "N/A",
                maintenance_date=m.maintenance_date.date(), # Convert datetime to date for schema
                description=(m.category_maintenance.cat_maintenance 
                             if m.category_maintenance and hasattr(m.category_maintenance, 'cat_maintenance') 
                             else (m.description if hasattr(m, 'description') else "N/A")), # Assuming 'description' field exists on Maintenance model as a fallback
                maintenance_cost=m.maintenance_cost, # Using the correct field name from model and schema
                provider=m.garage.nom_garage if m.garage and hasattr(m.garage, 'nom_garage') else (m.provider if hasattr(m, 'provider') else None) # Example
            ) for m in maintenance_q
        ]

    if "purchases" in categories:
        # Assuming models.Vehicle.purchase_date is DATETIME
        purchase_q = db.query(models.Vehicle).options(
            joinedload(models.Vehicle.make_ref), 
            joinedload(models.Vehicle.model_ref) 
        ).filter(
            models.Vehicle.purchase_date >= start_datetime,
            models.Vehicle.purchase_date <= end_datetime,
            models.Vehicle.purchase_price > 0 
        ).order_by(models.Vehicle.purchase_date.asc()).all()

        response_data.purchase_records = [
            schemas.PurchaseRecordDetail(
                id=v.id, 
                plate_number=v.plate_number,
                make=v.make_ref.vehicle_make if v.make_ref and hasattr(v.make_ref, 'vehicle_make') else "N/A",
                model=v.model_ref.vehicle_model if v.model_ref and hasattr(v.model_ref, 'vehicle_model') else "N/A",
                purchase_date=v.purchase_date.date() if v.purchase_date else None, # Convert datetime to date
                purchase_price=v.purchase_price
            ) for v in purchase_q
        ]
        
    return response_data