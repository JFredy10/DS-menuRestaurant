import os
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Mount the static and templates directories
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(str(DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Model for the product
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    imagen = Column(String)
    nombre = Column(String)
    descripcion = Column(String)
    imagen_path = Column(String)


# Create the database tables
Base.metadata.create_all(bind=engine)


# Home page
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Create product page
@app.get("/create")
def create_product(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})


# Create product endpoint
@app.post("/create")
async def create_product_endpoint(request: Request, id: int = Form(...), imagen: UploadFile = File(...),
                                  nombre: str = Form(...), descripcion: str = Form(...)):
    # Guardar la imagen en el servidor
    file_path = f"static/images/{imagen.filename}"
    with open(file_path, "wb") as file:
        contents = await imagen.read()
        file.write(contents)

    product = Product(id=id, imagen=imagen.filename, nombre=nombre, descripcion=descripcion, imagen_path=file_path)
    db = SessionLocal()
    db.add(product)
    db.commit()
    db.refresh(product)
    db.close()
    return templates.TemplateResponse("create.html", {"request": request, "message": "Product created successfully"})


# Read products page
@app.get("/read")
def read_products(request: Request, page: int = 1, limit: int = 10):
    db = SessionLocal()
    products = db.query(Product).offset((page - 1) * limit).limit(limit).all()
    db.close()
    return templates.TemplateResponse("read.html", {"request": request, "products": products})


# Update product page
@app.get("/update")
def update_product(request: Request):
    return templates.TemplateResponse("update.html", {"request": request})


# Update product endpoint
@app.post("/update")
def update_product_endpoint(request: Request, id: int = Form(...), imagen: UploadFile = File(...),
                            nombre: str = Form(...), descripcion: str = Form(...)):
    db = SessionLocal()
    product = db.query(Product).filter(Product.id == id).first()
    if product:
        # Guardar la nueva imagen en el servidor
        if imagen:
            file_path = f"static/images/{imagen.filename}"
            with open(file_path, "wb") as file:
                contents = imagen.file.read()
                file.write(contents)
            product.imagen = imagen.filename
            product.imagen_path = file_path
        product.nombre = nombre
        product.descripcion = descripcion
        db.commit()
        db.close()
        return templates.TemplateResponse("update.html",
                                          {"request": request, "message": "Product updated successfully"})
    else:
        db.close()
        return templates.TemplateResponse("update.html", {"request": request, "message": "Product not found"})


# Delete product page
@app.get("/delete")
def delete_product(request: Request):
    return templates.TemplateResponse("delete.html", {"request": request})


# Delete product endpoint
@app.post("/delete")
def delete_product_endpoint(request: Request, id: int = Form(...)):
    db = SessionLocal()
    product = db.query(Product).filter(Product.id == id).first()
    if product:
        # Eliminar la imagen del servidor
        if product.imagen_path:
            os.remove(product.imagen_path)
        db.delete(product)
        db.commit()
        db.close()
        return templates.TemplateResponse("delete.html",
                                          {"request": request, "message": "Product deleted successfully"})
    else:
        db.close()
        return templates.TemplateResponse("delete.html", {"request": request, "message": "Product not found"})


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
