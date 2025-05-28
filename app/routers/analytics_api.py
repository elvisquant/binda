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


# analytics_api.py

# ... (other code) ...

@router.get("/detailed-expense-records", response_model=schemas.DetailedReportDataResponse)
async def get_detailed_expense_records(
    start_date: DateType, 
    end_date: DateType,   
    categories: List[str] = Query(None, description="List of categories: fuel, reparation, maintenance, purchases"),
    db: Session = Depends(get_db)
):
    response_data = schemas.DetailedReportDataResponse()
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    if not categories:
        categories = ["fuel", "reparation", "maintenance", "purchases"]

    if "fuel" in categories:
        fuel_q = db.query(models.Fuel).options(
            joinedload(models.Fuel.vehicle)
        ).filter(
            models.Fuel.created_at >= start_datetime,
            models.Fuel.created_at <= end_datetime
        ).order_by(models.Fuel.created_at.asc()).all()
        
        temp_fuel_records = []
        for f in fuel_q:
            temp_fuel_records.append(schemas.FuelRecordDetail(
                id=f.id,
                vehicle_plate=f.vehicle.plate_number if f.vehicle and hasattr(f.vehicle, 'plate_number') else "N/A",
                date=f.created_at, # Schema expects datetime
                quantity=f.quantity if hasattr(f, 'quantity') else 0.0,
                cost=f.cost if hasattr(f, 'cost') else 0.0,
                notes=f.notes if hasattr(f, 'notes') else None
            ))
        response_data.fuel_records = temp_fuel_records

   

    if "reparation" in categories:
        reparation_q = db.query(models.Reparation).options(
            # Load the 'panne' relationship, and from 'panne', load its 'vehicle' relationship
            joinedload(models.Reparation.panne).joinedload(models.Panne.vehicle), 
            joinedload(models.Reparation.garage) 
        ).filter(
            models.Reparation.repair_date >= start_datetime,
            models.Reparation.repair_date <= end_datetime
        ).order_by(models.Reparation.repair_date.asc()).all()
        
        temp_reparation_records = []
        for r in reparation_q:
            vehicle_plate_for_reparation = "N/A"
            if r.panne and r.panne.vehicle and hasattr(r.panne.vehicle, 'plate_number'):
                vehicle_plate_for_reparation = r.panne.vehicle.plate_number

            reparation_description = "N/A"
            if r.panne and hasattr(r.panne, 'description') and r.panne.description:
                reparation_description = r.panne.description
            elif hasattr(r, 'description') and r.description: 
                 reparation_description = r.description

            provider_name = None
            if r.garage and hasattr(r.garage, 'nom_garage'):
                provider_name = r.garage.nom_garage
            elif hasattr(r, 'provider') and r.provider: 
                provider_name = r.provider

            temp_reparation_records.append(schemas.ReparationRecordDetail(
                id=r.id,
                vehicle_plate=vehicle_plate_for_reparation, # Use the derived plate number
                repair_date=r.repair_date.date() if r.repair_date else None,
                description=reparation_description,
                cost=r.cost if hasattr(r, 'cost') else 0.0,
                provider=provider_name
            ))
        response_data.reparation_records = temp_reparation_records



    if "maintenance" in categories:
        maintenance_q = db.query(models.Maintenance).options(
            joinedload(models.Maintenance.vehicle),
            joinedload(models.Maintenance.category_maintenance),
            joinedload(models.Maintenance.garage)
        ).filter(
            models.Maintenance.maintenance_date >= start_datetime,
            models.Maintenance.maintenance_date <= end_datetime
        ).order_by(models.Maintenance.maintenance_date.asc()).all()

        temp_maintenance_records = []
        for m in maintenance_q:
            maintenance_description = "N/A"
            if m.category_maintenance and hasattr(m.category_maintenance, 'cat_maintenance') and m.category_maintenance.cat_maintenance:
                maintenance_description = m.category_maintenance.cat_maintenance
            elif hasattr(m, 'description') and m.description: # Fallback if Maintenance model has its own description
                maintenance_description = m.description
            
            provider_name = None
            if m.garage and hasattr(m.garage, 'nom_garage'):
                provider_name = m.garage.nom_garage
            elif hasattr(m, 'provider') and m.provider: # Fallback if Maintenance model has its own provider
                provider_name = m.provider


            temp_maintenance_records.append(schemas.MaintenanceRecordDetail(
                id=m.id,
                vehicle_plate=m.vehicle.plate_number if m.vehicle and hasattr(m.vehicle, 'plate_number') else "N/A",
                maintenance_date=m.maintenance_date.date() if m.maintenance_date else None, # Schema expects date
                description=maintenance_description,
                # Ensure schema field name is 'maintenance_cost' if model is 'maintenance_cost'
                maintenance_cost=m.maintenance_cost if hasattr(m, 'maintenance_cost') else 0.0, 
                provider=provider_name
            ))
        response_data.maintenance_records = temp_maintenance_records

    if "purchases" in categories:
        purchase_q = db.query(models.Vehicle).options(
            joinedload(models.Vehicle.make_ref), 
            joinedload(models.Vehicle.model_ref) 
        ).filter(
            models.Vehicle.purchase_date >= start_datetime,
            models.Vehicle.purchase_date <= end_datetime,
            models.Vehicle.purchase_price > 0 
        ).order_by(models.Vehicle.purchase_date.asc()).all()

        temp_purchase_records = []
        for v in purchase_q:
            temp_purchase_records.append(schemas.PurchaseRecordDetail(
                id=v.id, 
                plate_number=v.plate_number if hasattr(v, 'plate_number') else "N/A",
                make=v.make_ref.vehicle_make if v.make_ref and hasattr(v.make_ref, 'vehicle_make') else "N/A",
                model=v.model_ref.vehicle_model if v.model_ref and hasattr(v.model_ref, 'vehicle_model') else "N/A",
                purchase_date=v.purchase_date.date() if v.purchase_date else None, # Schema expects date
                purchase_price=v.purchase_price if hasattr(v, 'purchase_price') else 0.0
            ))
        response_data.purchase_records = temp_purchase_records
        
    return response_data