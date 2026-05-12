from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.product import Product
from ..services.audit import AuditService
from ..utils.excel_import import import_products_from_excel
from pydantic import BaseModel

router = APIRouter()

class ProductCreate(BaseModel):
    name: str
    min_batch_size: float
    max_batch_size: float
    ade_pde: float
    min_dose: float
    max_dose: float
    swab_recovery: float
    lod: float
    loq: float
    swab_dilution: float
    swab_surface_area: float = 0.01
    solubility: str
    hardest_to_clean: str
    plant: str

@router.get("/")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@router.post("/")
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}")
def update_product(product_id: int, product_data: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product_data.dict().items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}

@router.post("/import")
async def import_products(file: UploadFile = File(...), db: Session = Depends(get_db)):
    result = await import_products_from_excel(file, db)
    return result