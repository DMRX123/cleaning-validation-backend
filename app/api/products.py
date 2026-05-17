# app/api/products.py - COMPLETE FINAL VERSION

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.product import Product
from ..services.audit import AuditService
from ..utils.excel_import import import_products_from_excel
from .auth import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# ==================== SCHEMAS ====================

class ProductCreate(BaseModel):
    name: str
    product_code: Optional[str] = None
    min_batch_size: float
    max_batch_size: float
    ade_pde: float
    min_dose: float
    max_dose: float
    swab_recovery: float = 70
    lod: float = 0.1
    loq: float = 0.5
    swab_dilution: float = 20
    swab_surface_area: float = 0.01
    solubility: str
    hardest_to_clean: str
    plant: str
    toxicity_class: int = 3
    potency_class: int = 3
    cleanability_rating: int = 2

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    product_code: Optional[str] = None
    min_batch_size: Optional[float] = None
    max_batch_size: Optional[float] = None
    ade_pde: Optional[float] = None
    min_dose: Optional[float] = None
    max_dose: Optional[float] = None
    swab_recovery: Optional[float] = None
    lod: Optional[float] = None
    loq: Optional[float] = None
    swab_dilution: Optional[float] = None
    swab_surface_area: Optional[float] = None
    solubility: Optional[str] = None
    hardest_to_clean: Optional[str] = None
    plant: Optional[str] = None
    toxicity_class: Optional[int] = None
    potency_class: Optional[int] = None
    cleanability_rating: Optional[int] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    product_code: Optional[str] = None
    min_batch_size: float
    max_batch_size: float
    ade_pde: float
    min_dose: float
    max_dose: float
    swab_recovery: float
    lod: float
    loq: float
    swab_dilution: float
    swab_surface_area: float
    solubility: str
    hardest_to_clean: str
    plant: str
    toxicity_class: Optional[int] = None
    potency_class: Optional[int] = None
    cleanability_rating: Optional[int] = None
    batch_size_display: Optional[str] = None
    ade_display: Optional[str] = None
    tdd_display: Optional[str] = None
    
    class Config:
        from_attributes = True

# ==================== ENDPOINTS ====================

@router.get("/", response_model=List[ProductResponse])
def get_products(
    plant: Optional[str] = Query(None, description="Filter by plant"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Product)
    if plant:
        query = query.filter(Product.plant == plant)
    products = query.all()
    
    # Add computed properties
    for p in products:
        p.batch_size_display = p.batch_size_display
        p.ade_display = p.ade_display
        p.tdd_display = p.tdd_display
    
    return products


@router.get("/by-plant/{plant_name}", response_model=List[ProductResponse])
def get_products_by_plant(
    plant_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    products = db.query(Product).filter(Product.plant == plant_name).all()
    if not products:
        raise HTTPException(status_code=404, detail=f"No products found in {plant_name}")
    
    for p in products:
        p.batch_size_display = p.batch_size_display
        p.ade_display = p.ade_display
        p.tdd_display = p.tdd_display
    
    return products


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    existing = db.query(Product).filter(Product.name == product.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product name already exists")
    
    product_code = product.product_code
    if not product_code:
        product_code = product.name[:6].upper().replace(" ", "")
    
    new_product = Product(
        name=product.name,
        product_code=product_code,
        min_batch_size=product.min_batch_size,
        max_batch_size=product.max_batch_size,
        ade_pde=product.ade_pde,
        min_dose=product.min_dose,
        max_dose=product.max_dose,
        swab_recovery=product.swab_recovery,
        lod=product.lod,
        loq=product.loq,
        swab_dilution=product.swab_dilution,
        swab_surface_area=product.swab_surface_area,
        solubility=product.solubility,
        hardest_to_clean=product.hardest_to_clean,
        plant=product.plant,
        toxicity_class=product.toxicity_class,
        potency_class=product.potency_class,
        cleanability_rating=product.cleanability_rating
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    AuditService.log(db, current_user.id, "CREATE", "Product", new_product.id, None, new_product.__dict__)
    
    new_product.batch_size_display = new_product.batch_size_display
    new_product.ade_display = new_product.ade_display
    new_product.tdd_display = new_product.tdd_display
    
    return new_product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.batch_size_display = product.batch_size_display
    product.ade_display = product.ade_display
    product.tdd_display = product.tdd_display
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_values = product.__dict__.copy()
    
    update_dict = product_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    
    AuditService.log(db, current_user.id, "UPDATE", "Product", product.id, old_values, product.__dict__)
    
    product.batch_size_display = product.batch_size_display
    product.ade_display = product.ade_display
    product.tdd_display = product.tdd_display
    
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_values = product.__dict__.copy()
    db.delete(product)
    db.commit()
    
    AuditService.log(db, current_user.id, "DELETE", "Product", product_id, old_values, None)
    
    return {"message": "Product deleted successfully"}


@router.post("/import")
async def import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await import_products_from_excel(file, db)
    return result


@router.get("/plant/{plant_name}/worst-case")
def get_plant_worst_case(
    plant_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from ..services.worst_case_service import WorstCaseService
    
    products = db.query(Product).filter(Product.plant == plant_name).all()
    if not products:
        raise HTTPException(404, f"No products found in {plant_name}")
    
    worst_case = WorstCaseService.select_worst_case(products)
    if not worst_case:
        raise HTTPException(404, "Could not determine worst case product")
    
    rating = WorstCaseService.calculate_product_rating(worst_case)
    
    return {
        "plant": plant_name,
        "worst_case_product": {
            "id": worst_case.id,
            "name": worst_case.name,
            "product_code": worst_case.product_code,
            "batch_size_kg": worst_case.min_batch_size,
            "ade_pde_ug": worst_case.ade_pde,
            "min_dose_mg": worst_case.min_dose,
            "solubility": worst_case.solubility,
            "hardest_to_clean": worst_case.hardest_to_clean
        },
        "rating": rating,
        "recommendation": f"Use {worst_case.name} as worst case for cleaning validation in {plant_name}"
    }


@router.get("/plant/{plant_name}/all-with-ratings")
def get_all_products_with_ratings(
    plant_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from ..services.worst_case_service import WorstCaseService
    
    products = db.query(Product).filter(Product.plant == plant_name).all()
    if not products:
        raise HTTPException(404, f"No products found in {plant_name}")
    
    ratings = []
    for product in products:
        rating = WorstCaseService.calculate_product_rating(product)
        ratings.append(rating)
    
    # Sort by total rating (highest first)
    ratings.sort(key=lambda x: x["total_rating"], reverse=True)
    
    return {
        "plant": plant_name,
        "total_products": len(products),
        "products_ranking": ratings,
        "worst_case": ratings[0] if ratings else None
    }