from sqlalchemy import Column, DateTime, Integer, String,Float, ForeignKey, TIMESTAMP, text, Enum as DBEnum # Added DBEnum
from datetime import datetime # For default values or type hinting if needed
import enum # For Python enum
from typing import List, Optional
from datetime import datetime, date , timedelta
from pydantic import BaseModel
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.sql import func # For default timestamps
from .database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False) # Added length for clarity
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False) # Hashed password
    
    # MODIFIED: Replaced is_active with status
    status = Column(String(50), nullable=False, default="pending_approval") # e.g., "active", "inactive", "pending_approval"
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    # You might want to add roles or other fields later
    # role = Column(String(50), default="user") 
    # Add other fields as needed (e.g., is_superuser, roles, etc.)
##################################################################################################################

class Driver(Base):
    __tablename__ = "driver"
    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    cni_number = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    matricule = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
##################################################################################################################


class VehicleType(Base):
    __tablename__ = "vehicle_type"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_type = Column(String, nullable=False)
##################################################################################################################

class VehicleMake(Base):
    __tablename__ = "vehicle_make"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_make = Column(String, nullable=False)
##################################################################################################################

class VehicleModel(Base):
    __tablename__ = "vehicle_model"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_model = Column(String, nullable=False)
##################################################################################################################

class VehicleTransmission(Base):
    __tablename__ = "vehicle_transmission"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_transmission = Column(String, nullable=False)
##################################################################################################################


class FuelType(Base):
    __tablename__ = "fuel_type" # Singular as established
    id = Column(Integer, primary_key=True, index=True)
    fuel_type = Column(String, unique=True, index=True, nullable=False) # The name like "Petrol", "Diesel"
    # Optional: Add a description or other relevant fields
    # description = Column(String, nullable=True)

#########################################################################################################################

class Fuel(Base):
    __tablename__ = "fuel" # This table name can be singular or plural as you prefer

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys now correctly point to singular table names
    vehicle_id = Column(Integer, ForeignKey("vehicle.id", ondelete="CASCADE"), nullable=False)
    fuel_type_id = Column(Integer, ForeignKey("fuel_type.id", ondelete="CASCADE"), nullable=False)

    quantity = Column(Float, nullable=False)
    price_little = Column(Float, nullable=False) # Price per Liter/Unit
    cost = Column(Float, nullable=False)         # Total cost (quantity * price_little)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    # updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'), onupdate=text('now()'))

    vehicle = relationship("Vehicle")
    #fuel_type=relationship("fuel_type")

##################################################################################################################################
class Vehicle(Base):
    __tablename__ = "vehicle"
    id = Column(Integer, primary_key=True, index=True)
    make = Column(Integer, ForeignKey("vehicle_make.id"))
    model = Column(Integer, ForeignKey("vehicle_model.id"))
    year = Column(Integer)
    plate_number = Column(String, unique=True, nullable=False)
    mileage = Column(Float, default=0.0)
    engine_size = Column(Float, default=0.0)
    vehicle_type = Column(Integer, ForeignKey("vehicle_type.id"))
    vehicle_transmission = Column(Integer, ForeignKey("vehicle_transmission.id"))
    vehicle_fuel_type = Column(Integer, ForeignKey("fuel_type.id"))
    vin = Column(String, nullable=False)
    color = Column(String, nullable=False)
    purchase_price = Column(Float, default=0.0)
    purchase_date = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(String, default="available")
    registration_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()')) 

     
    make_ref = relationship("VehicleMake") # Points to VehicleMake class
    model_ref = relationship("VehicleModel") # Points to VehicleModel class


##################################################################################################################

class CategoryDocument(Base):
    __tablename__ = "category_document"
    id = Column(Integer, primary_key=True, index=True)
    doc_name = Column(String, nullable=False)
    cost = Column(Float, default=0.0)
##################################################################################################################

class DocumentVehicule(Base):
    __tablename__ = "document_vehicule"
    id = Column(Integer, primary_key=True, index=True)
    doc_name_id = Column(Integer, ForeignKey("category_document.id"))
    vehicule_id = Column(Integer, ForeignKey("vehicle.id"))
    issued_date = Column(TIMESTAMP(timezone=True), nullable=False)
    expiration_date = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
##################################################################################################################

class Garage(Base):
    __tablename__ = "garage"
    id = Column(Integer, primary_key=True, index=True)
    nom_garage = Column(String, nullable=False)
##################################################################################################################

class CategoryMaintenance(Base):
    __tablename__ = "category_maintenance"
    id = Column(Integer, primary_key=True, index=True)
    cat_maintenance = Column(String, nullable=False)
##################################################################################################################
  
class Maintenance(Base):
    __tablename__ = "maintenance"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Foreign Keys
    cat_maintenance_id = Column(Integer, ForeignKey("category_maintenance.id", ondelete="SET NULL"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle.id", ondelete="CASCADE"), nullable=False) # ForeignKey references 'vehicle.id'
    garage_id = Column(Integer, ForeignKey("garage.id", ondelete="SET NULL"), nullable=True)
    maintenance_cost = Column(Float, default=0.0, nullable=False)
    receipt = Column(String, nullable=False)
    maintenance_date = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    status = Column(String(50), default="active", nullable=False) # Added max length, nullable=False
    
    
  
    vehicle = relationship("Vehicle") 
    category_maintenance = relationship("CategoryMaintenance")
    garage = relationship("Garage")

   
##################################################################################################################

class CategoryPanne(Base):
    __tablename__ = "category_panne"
    id = Column(Integer, primary_key=True, index=True)
    panne_name = Column(String, nullable=False)
##################################################################################################################

class Panne(Base):
    __tablename__ = "panne"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"), nullable=False) # Make nullable=False explicit
    category_panne_id = Column(Integer, ForeignKey("category_panne.id"), nullable=False) # Make nullable=False explicit
    description = Column(String(500), nullable=True) # Added max length matching schema
    status = Column(String(50), default="active", nullable=False) # Added max length, nullable=False
    panne_date = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Define relationships for joinedload to work effectively for PanneOut
    # Ensure 'Vehicle' and 'CategoryPanne' are the correct class names of your SQLAlchemy models
    # and that they have corresponding 'pannes' back_populates if you want bi-directional.
    vehicle = relationship("Vehicle") # lazy="joined" can also work like joinedload by default
    category_panne = relationship("CategoryPanne")


##################################################################################################################

class Reparation(Base):
    __tablename__ = "reparation"
    id = Column(Integer, primary_key=True, index=True)
    panne_id = Column(Integer, ForeignKey("panne.id"))
    cost = Column(Float, default=0.0)
    receipt = Column(String, nullable=False)
    garage_id = Column(Integer, ForeignKey("garage.id"))
    repair_date = Column(TIMESTAMP(timezone=True), nullable=False)
    status = Column(String, default="Inprogress")

    panne = relationship("Panne") # backref can be added in Panne if needed
    garage = relationship("Garage") # backref can be added in Garage if needed
    # created_by = relationship("User") # If you add created_by_user_id

#########################################################################################################################

class Trip(Base):
    __tablename__ = "trip"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("driver.id"), nullable=False)
    start_location = Column(String, nullable=False)
    end_location = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True) # Can be null if trip is ongoing/planned

    # --- NEW FIELDS ---
    purpose = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    # --- END NEW FIELDS ---

    status = Column(String, nullable=False, default="planned") # e.g., planned, ongoing, completed, cancelled

    # Assuming you have a way to track when the trip record was created
    # This is good practice but not strictly related to 'purpose' and 'notes'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships (if not already defined)
    vehicle = relationship("Vehicle") # Replace "Vehicle" with your actual Vehicle model name
    driver = relationship("Driver")   # Replace "Driver" with your actual Driver model name

    # If you have other fields like distance, estimated_duration, etc., keep them.







# Add these to your analytics_api.py, likely near other Pydantic models

class FuelRecordDetail(BaseModel):
    id: int
    vehicle_plate: Optional[str] = "N/A" # Assuming you can join to Vehicle
    date: datetime # Or date_type depending on your model.Fuel.created_at
    quantity: float
    cost: float
    notes: Optional[str] = None

    class Config:
        orm_mode = True # For Pydantic V1
        # from_attributes = True # For Pydantic V2

class ReparationRecordDetail(BaseModel):
    id: int
    vehicle_plate: Optional[str] = "N/A"
    repair_date: date
    description: str
    cost: float
    provider: Optional[str] = None

    class Config:
        orm_mode = True
        # from_attributes = True

class MaintenanceRecordDetail(BaseModel):
    id: int
    vehicle_plate: Optional[str] = "N/A"
    maintenance_date: date
    description: str # Or category name
    cost: float
    provider: Optional[str] = None

    class Config:
        orm_mode = True
        # from_attributes = True

class PurchaseRecordDetail(BaseModel): # For vehicle purchases
    id: int # Vehicle ID
    plate_number: str
    make: Optional[str] = "N/A"
    model: Optional[str] = "N/A"
    purchase_date: Optional[date] = None
    purchase_price: Optional[float] = 0.0

    class Config:
        orm_mode = True
        # from_attributes = True


class DetailedReportDataResponse(BaseModel):
    fuel_records: List[FuelRecordDetail] = []
    reparation_records: List[ReparationRecordDetail] = []
    maintenance_records: List[MaintenanceRecordDetail] = []
    purchase_records: List[PurchaseRecordDetail] = [] # Vehicle purchases  