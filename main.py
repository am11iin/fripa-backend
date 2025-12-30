from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product, Order
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import uuid
import shutil

app = FastAPI(title="Fripa API", version="1.0.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Accepte toutes les origines
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Ajout OPTIONS
    allow_headers=["*"],  # Accepte tous les headers
)

# Servir les fichiers statiques (images)
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

ADMIN_PASSWORD = "fripaAdmin123"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def authenticate_admin(admin_session: str = Header(None)):
    if admin_session != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Accès refusé : Authentification administrateur requise")

# --- Pydantic Schemas ---
class ProductSchema(BaseModel):
    id: Optional[int]
    name: str
    description: str
    price: float
    image_url: str
    class Config:
        orm_mode = True
        from_attributes = True

class ProductCreateSchema(BaseModel):
    name: str
    description: Optional[str] = ""
    price: float
    image_url: str

class OrderSchema(BaseModel):
    id: Optional[int]
    user_name: str
    user_email: str
    user_phone: str
    user_address: str
    products: str
    class Config:
        orm_mode = True
        from_attributes = True

class OrderCreateSchema(BaseModel):
    user_name: str
    user_email: str
    user_phone: str
    user_address: str
    products: List[int]

class CartItemSchema(BaseModel):
    product_id: int
    quantity: int

class CheckoutSchema(BaseModel):
    cart: List[dict]
    user_name: str
    user_email: str
    user_phone: str
    user_address: str

# --- API Routes ---
@app.get("/")
def read_root():
    return {"message": "Bienvenue sur le backend de Fripa!"}

@app.get("/products", response_model=List[ProductSchema])
def read_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.post("/products", response_model=ProductSchema)
def create_product(product: ProductCreateSchema, admin_session: str = Header(None), db: Session = Depends(get_db)):
    authenticate_admin(admin_session)
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/{product_id}", response_model=ProductSchema)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, admin_session: str = Header(None), db: Session = Depends(get_db)):
    authenticate_admin(admin_session)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    db.delete(product)
    db.commit()
    return {"message": "Produit supprimé avec succès"}

@app.put("/products/{product_id}", response_model=ProductSchema)
def update_product(product_id: int, product: ProductCreateSchema, admin_session: str = Header(None), db: Session = Depends(get_db)):
    authenticate_admin(admin_session)
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/search", response_model=List[ProductSchema])
def search_products(query: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    products_query = db.query(Product)
    if query:
        products_query = products_query.filter(Product.name.ilike(f"%{query}%"))
    if category:
        products_query = products_query.filter(Product.description.ilike(f"%{category}%"))
    return products_query.all()

@app.post("/cart")
def add_to_cart(item: CartItemSchema, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return {"message": "Produit ajouté au panier", "product": ProductSchema.model_validate(product), "quantity": item.quantity}

@app.post("/checkout")
def checkout(data: CheckoutSchema, db: Session = Depends(get_db)):
    order = Order(
        user_name=data.user_name,
        user_email=data.user_email,
        user_phone=data.user_phone,
        user_address=data.user_address,
        products=json.dumps(data.cart)
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"message": "Commande validée", "order_id": order.id}

@app.get("/admin/orders", response_model=List[OrderSchema])
def read_admin_orders(admin_session: str = Header(None), db: Session = Depends(get_db)):
    authenticate_admin(admin_session)
    return db.query(Order).all()

@app.post("/orders", response_model=OrderSchema)
def create_order(order: OrderCreateSchema, db: Session = Depends(get_db)):
    db_order = Order(
        user_name=order.user_name,
        user_email=order.user_email,
        user_phone=order.user_phone,
        user_address=order.user_address,
        products=json.dumps(order.products)
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

# --- Upload d'images ---
@app.post("/upload-images")
async def upload_images(
    files: List[UploadFile] = File(...),
    admin_session: str = Header(None)
):
    authenticate_admin(admin_session)
    
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 images autorisées")
    
    uploaded_files = []
    
    for file in files:
        # Vérifier le type de fichier
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"Le fichier {file.filename} n'est pas une image")
        
        # Générer un nom unique
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"uploads/{unique_filename}"
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        uploaded_files.append(f"/uploads/{unique_filename}")
    
    return {"images": uploaded_files}

@app.post("/products-with-images", response_model=ProductSchema)
def create_product_with_images(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    admin_session: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    if admin_session != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Accès refusé : Authentification administrateur requise")
    
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 images autorisées")
    
    # Upload des images
    uploaded_images = []
    for file in files:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"Le fichier {file.filename} n'est pas une image")
        
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"uploads/{unique_filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        uploaded_images.append(f"/uploads/{unique_filename}")
    
    # Créer le produit
    product_data = {
        "name": name,
        "description": description,
        "price": price,
        "image_url": uploaded_images[0] if uploaded_images else "",
        "images": json.dumps(uploaded_images)  # Stocker en JSON
    }
    
    db_product = Product(**product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Retourner le produit avec les images parsées
    product_dict = {
        "id": db_product.id,
        "name": db_product.name,
        "description": db_product.description,
        "price": db_product.price,
        "image_url": db_product.image_url,
        "images": json.loads(db_product.images) if db_product.images else []
    }
    
    return ProductSchema(**product_dict)