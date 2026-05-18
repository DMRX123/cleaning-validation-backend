# app/api/products.py - COMPLETE FIXED VERSION

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.product import Product
from ..services.audit import AuditService
from ..utils.excel_import import import_products_from_excel
from .auth import get_current_user
from ..schemas.product import ProductCreate, ProductUpdate, ProductResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[ProductResponse])
def get_products(
    plant: Optional[str] = Query(None, description="Filter by plant"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all products with optional plant filter"""
    try:
        query = db.query(Product)
        if plant:
            query = query.filter(Product.plant == plant)
        products = query.all()
        
        result = []
        for p in products:
            result.append({
                "id": p.id,
                "name": p.name,
                "product_code": p.product_code,
                "min_batch_size": p.min_batch_size,
                "max_batch_size": p.max_batch_size,
                "ade_pde": p.ade_pde,
                "min_dose": p.min_dose,
                "max_dose": p.max_dose,
                "swab_recovery": p.swab_recovery,
                "lod": p.lod,
                "loq": p.loq,
                "swab_dilution": p.swab_dilution,
                "swab_surface_area": p.swab_surface_area,
                "solubility": p.solubility,
                "hardest_to_clean": p.hardest_to_clean,
                "plant": p.plant,
                "toxicity_class": p.toxicity_class,
                "potency_class": p.potency_class,
                "cleanability_rating": p.cleanability_rating,
                "batch_size_display": p.batch_size_display,
                "ade_display": p.ade_display,
                "tdd_display": p.tdd_display
            })
        return result
    except Exception as e:
        logger.error(f"Products endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-plant/{plant_name}", response_model=List[ProductResponse])
def get_products_by_plant(
    plant_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get products filtered by plant - APIC Section 7.2 compliant - FIXED"""
    try:
        products = db.query(Product).filter(Product.plant == plant_name).all()
        if not products:
            # Return empty list instead of 404
            return []
        
        result = []
        for p in products:
            result.append({
                "id": p.id,
                "name": p.name,
                "product_code": p.product_code,
                "min_batch_size": p.min_batch_size,
                "max_batch_size": p.max_batch_size,
                "ade_pde": p.ade_pde,
                "min_dose": p.min_dose,
                "max_dose": p.max_dose,
                "swab_recovery": p.swab_recovery,
                "lod": p.lod,
                "loq": p.loq,
                "swab_dilution": p.swab_dilution,
                "swab_surface_area": p.swab_surface_area,
                "solubility": p.solubility,
                "hardest_to_clean": p.hardest_to_clean,
                "plant": p.plant,
                "toxicity_class": p.toxicity_class,
                "potency_class": p.potency_class,
                "cleanability_rating": p.cleanability_rating,
                "batch_size_display": p.batch_size_display,
                "ade_display": p.ade_display,
                "tdd_display": p.tdd_display
            })
        return result
    except Exception as e:
        logger.error(f"Products by plant endpoint error: {str(e)}")
        return []


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
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
        
        return {
            "id": new_product.id,
            "name": new_product.name,
            "product_code": new_product.product_code,
            "min_batch_size": new_product.min_batch_size,
            "max_batch_size": new_product.max_batch_size,
            "ade_pde": new_product.ade_pde,
            "min_dose": new_product.min_dose,
            "max_dose": new_product.max_dose,
            "swab_recovery": new_product.swab_recovery,
            "lod": new_product.lod,
            "loq": new_product.loq,
            "swab_dilution": new_product.swab_dilution,
            "swab_surface_area": new_product.swab_surface_area,
            "solubility": new_product.solubility,
            "hardest_to_clean": new_product.hardest_to_clean,
            "plant": new_product.plant,
            "toxicity_class": new_product.toxicity_class,
            "potency_class": new_product.potency_class,
            "cleanability_rating": new_product.cleanability_rating,
            "batch_size_display": new_product.batch_size_display,
            "ade_display": new_product.ade_display,
            "tdd_display": new_product.tdd_display
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create product error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "id": product.id,
            "name": product.name,
            "product_code": product.product_code,
            "min_batch_size": product.min_batch_size,
            "max_batch_size": product.max_batch_size,
            "ade_pde": product.ade_pde,
            "min_dose": product.min_dose,
            "max_dose": product.max_dose,
            "swab_recovery": product.swab_recovery,
            "lod": product.lod,
            "loq": product.loq,
            "swab_dilution": product.swab_dilution,
            "swab_surface_area": product.swab_surface_area,
            "solubility": product.solubility,
            "hardest_to_clean": product.hardest_to_clean,
            "plant": product.plant,
            "toxicity_class": product.toxicity_class,
            "potency_class": product.potency_class,
            "cleanability_rating": product.cleanability_rating,
            "batch_size_display": product.batch_size_display,
            "ade_display": product.ade_display,
            "tdd_display": product.tdd_display
        }
    except Exception as e:
        logger.error(f"Get product error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        old_values = product.__dict__.copy()
        
        # Only update fields that are provided (not None)
        update_dict = product_data.model_dump(exclude_unset=True)
        
        # Log what we're updating
        logger.info(f"Updating product {product_id} with: {update_dict.keys()}")
        
        for key, value in update_dict.items():
            if value is not None and hasattr(product, key):
                setattr(product, key, value)
        
        db.commit()
        db.refresh(product)
        
        AuditService.log(db, current_user.id, "UPDATE", "Product", product.id, old_values, product.__dict__)
        
        return {
            "id": product.id,
            "name": product.name,
            "product_code": product.product_code,
            "min_batch_size": product.min_batch_size,
            "max_batch_size": product.max_batch_size,
            "ade_pde": product.ade_pde,
            "min_dose": product.min_dose,
            "max_dose": product.max_dose,
            "swab_recovery": product.swab_recovery,
            "lod": product.lod,
            "loq": product.loq,
            "swab_dilution": product.swab_dilution,
            "swab_surface_area": product.swab_surface_area,
            "solubility": product.solubility,
            "hardest_to_clean": product.hardest_to_clean,
            "plant": product.plant,
            "toxicity_class": product.toxicity_class,
            "potency_class": product.potency_class,
            "cleanability_rating": product.cleanability_rating,
            "batch_size_display": product.batch_size_display,
            "ade_display": product.ade_display,
            "tdd_display": product.tdd_display
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update product error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        old_values = product.__dict__.copy()
        db.delete(product)
        db.commit()
        
        AuditService.log(db, current_user.id, "DELETE", "Product", product_id, old_values, None)
        
        return {"message": "Product deleted successfully"}
    except Exception as e:
        logger.error(f"Delete product error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")


@router.post("/import")
def import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Import products from Excel file"""
    try:
        result = import_products_from_excel(file, db)
        return result
    except Exception as e:
        logger.error(f"Import products error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
    
    ratings.sort(key=lambda x: x["total_rating"], reverse=True)
    
    return {
        "plant": plant_name,
        "total_products": len(products),
        "products_ranking": ratings,
        "worst_case": ratings[0] if ratings else None
    }