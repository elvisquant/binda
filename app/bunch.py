
#This is to get fuel type
router = APIRouter(prefix="/fuel_type", tags=['Fuel Type'])
@router.get("/", response_model = List[schemas.FuelTypeOut])
def get_type_fuel(db:Session = Depends(get_db),limit : int = 10, skip : int = 0, search :Optional[str] = ""):
    ##filter all type of fuel at the same time
    type_fuels = db.query(models.FuelType).filter(models.FuelType.fuel_type.contains(search)).limit(limit).offset(skip).all()
    return type_fuels 

#This is to get garage
router = APIRouter(prefix="/garage", tags=['Garage'])
@router.get("/", response_model = List[schemas.GarageOut])
def get_garage(db:Session = Depends(get_db),limit : int = 20, skip : int = 0, search :Optional[str] = ""):
              
  
    ##filter all garages at the same time
    garages = db.query(models.Garage).filter(models.Garage.nom_garage.contains(search)).limit(limit).offset(skip).all()
    return garages

#This is to get category maintenance
router = APIRouter(prefix="/category_maintenance", tags=['Category aintenance'])
@router.get("/", response_model = List[schemas.CategoryMaintenanceOut])
def get_caat_maintenance(db:Session = Depends(get_db),limit : int = 5, skip : int = 0, search :Optional[str] = ""):
    ##filter all maintenance categories at the same time
    maintenance_categories = db.query(models.CategoryMaintenance).filter(models.CategoryMaintenance.cat_maintenance.contains(search)).limit(limit).offset(skip).all()
    return maintenance_categories

#this is to get  category panne
router = APIRouter(prefix="/category_panne", tags=['Category Panne'])
@router.get("/", response_model = List[schemas.CategoryPanneOut])
def get_panne_categories(db:Session = Depends(get_db),limit : int = 20, skip : int = 0, search :Optional[str] = ""):
    ##filter all panne categories at the same time
    pannes = db.query(models.CategoryPanne).filter(models.CategoryPanne.panne_name.contains(search)).limit(limit).offset(skip).all()
    return pannes

#This is to get vehicle transmission
router = APIRouter(prefix="/vehicle_transmission", tags=['Vehicle Transmission'])
@router.get("/", response_model = List[schemas.VehicleTransmissionOut])
def get_vehicles_transmission(db:Session = Depends(get_db),limit : int = 10, skip : int = 0, search :Optional[str] = ""):
    ##filter all vehicles transmission at the same time
    veh_transmission = db.query(models.VehicleTransmission).filter(models.VehicleTransmission.vehicle_transmission.contains(search)).limit(limit).offset(skip).all()
    return veh_transmission 

#This is to get vehicle make
router = APIRouter(prefix="/vehicle_make", tags=['Vehicle Make'])

@router.get("/", response_model = List[schemas.VehicleMakeOut])
def get_vehicles_make(db:Session = Depends(get_db),limit : int = 10, skip : int = 0, search :Optional[str] = ""):
    ##filter all Vehicle Make at the same time
    vehicles_make= db.query(models.VehicleMake).filter(models.VehicleMake.vehicle_make.contains(search)).limit(limit).offset(skip).all()
    return vehicles_make 

#This is to get vehicle model
router = APIRouter(prefix="/vehicle_model", tags=['Vehicle Model'])
@router.get("/", response_model = List[schemas.VehicleModelOut])
def get_veh_models(db:Session = Depends(get_db),limit : int = 10, skip : int = 0, search :Optional[str] = ""):
    ##filter all vehicle Models at the same time
    veh_models = db.query(models.VehicleModel).filter(models.VehicleModel.vehicle_model.contains(search)).limit(limit).offset(skip).all()
    return veh_models

#This is to get vehicle type
router = APIRouter(prefix="/vehicle_type", tags=['Vehicle Type'])
@router.get("/", response_model = List[schemas.VehicleTypeOut])
def get_vehicle_types(db:Session = Depends(get_db),limit : int = 10, skip : int = 0, search :Optional[str] = ""):
    ##filter all vehicle types at the same time
    veh_types = db.query(models.VehicleType).filter(models.VehicleType.vehicle_type.contains(search)).limit(limit).offset(skip).all()
    return veh_types