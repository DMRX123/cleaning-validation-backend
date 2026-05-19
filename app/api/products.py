from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.product import Product
from ..utils.excel_import import import_products_from_excel
from ..schemas.product import ProductCreate, ProductUpdate, ProductResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# ALL ENDPOINTS PUBLIC - NO AUTHENTICATION
# ============================================

@router.get("/", response_model=List[ProductResponse])
def get_products(
    plant: Optional[str] = Query(None, description="Filter by plant"),
    db: Session = Depends(get_db)
):
    """Get all products with optional plant filter - PUBLIC"""
    try:
        query = db.query(Product)
        if plant:
            query = query.filter(Product.plant == plant)
        products = query.all()
        return products
    except Exception as e:
        logger.error(f"Products endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product - PUBLIC"""
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
        
        return new_product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create product error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")


@router.post("/import")
def import_products(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import products from Excel file - PUBLIC"""
    try:
        result = import_products_from_excel(file, db)
        return result
    except Exception as e:
        logger.error(f"Import products error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID - PUBLIC"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except Exception as e:
        logger.error(f"Get product error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product_data: ProductUpdate, db: Session = Depends(get_db)):
    """Update a product by ID - PUBLIC"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        update_dict = product_data.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            if value is not None and hasattr(product, key):
                setattr(product, key, value)
        
        db.commit()
        db.refresh(product)
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update product error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product by ID - PUBLIC"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        db.delete(product)
        db.commit()
        
        return {"message": "Product deleted successfully", "id": product_id, "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete product error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")


@router.delete("/all")
def delete_all_products(db: Session = Depends(get_db)):
    """Delete ALL products - PUBLIC"""
    try:
        count = db.query(Product).delete()
        db.commit()
        return {"success": True, "message": f"Deleted {count} products", "deleted_count": count}
    except Exception as e:
        logger.error(f"Delete all products error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-plant/{plant_name}", response_model=List[ProductResponse])
def get_products_by_plant(plant_name: str, db: Session = Depends(get_db)):
    """Get products filtered by plant - PUBLIC"""
    try:
        products = db.query(Product).filter(Product.plant == plant_name).all()
        return products
    except Exception as e:
        logger.error(f"Products by plant endpoint error: {str(e)}")
        return []


@router.get("/plant/{plant_name}/worst-case")
def get_plant_worst_case(plant_name: str, db: Session = Depends(get_db)):
    """Get worst case product for a plant - PUBLIC"""
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
def get_all_products_with_ratings(plant_name: str, db: Session = Depends(get_db)):
    """Get all products with worst case ratings - PUBLIC"""
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


@router.get("/all/details")
def get_all_products_detailed(db: Session = Depends(get_db)):
    """Get all products with full details - PUBLIC"""
    try:
        products = db.query(Product).all()
        return {
            "success": True,
            "count": len(products),
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "product_code": p.product_code,
                    "batch_size_kg": p.min_batch_size,
                    "ade_pde_ug": p.ade_pde,
                    "min_dose_mg": p.min_dose,
                    "max_dose_mg": p.max_dose,
                    "solubility": p.solubility,
                    "hardest_to_clean": p.hardest_to_clean,
                    "plant": p.plant,
                    "swab_recovery": p.swab_recovery,
                    "lod_ppm": p.lod,
                    "loq_ppm": p.loq,
                    "swab_dilution_ml": p.swab_dilution,
                    "toxicity_class": p.toxicity_class,
                    "potency_class": p.potency_class
                }
                for p in products
            ]
        }
    except Exception as e:
        logger.error(f"Get all products detailed error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))