
from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path

from database import get_db
from models import Shop, Product, Order
from webhook import router as webhook_router
from schemas import OrderCreate


app = FastAPI(
    title="Instagram Social Commerce Agent",
    description="AI-powered Instagram DM automation",
    version="1.0.0",
)


# Static uploads directory
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"

print("Upload directory:", UPLOAD_DIR)
print("Directory exists:", UPLOAD_DIR.exists())
print(
    "Image exists:",
    (UPLOAD_DIR / "products" / "tshirt001.jpg").exists()
)

app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads"
)


@app.get("/")
async def home():
    return {
        "status": "running",
        "message": "Instagram Social Commerce Agent is running!",
    }


@app.get("/shops")
def get_shops(db: Session = Depends(get_db)):
    return db.query(Shop).all()


@app.get("/shops/{shop_id}")
def get_shop(shop_id: int, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()

    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    return shop


@app.get("/shops/{shop_id}/products")
def get_shop_products(
    shop_id: int,
    db: Session = Depends(get_db),
):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()

    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    return db.query(Product).filter(Product.shop_id == shop_id).all()


@app.post("/orders", status_code=201)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(
            Product.id == order_data.product_id,
            Product.shop_id == order_data.shop_id,
        )
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.is_configurable:
        if product.sizes and order_data.selected_size not in product.sizes:
            raise HTTPException(status_code=400, detail="Invalid size")

        if product.colors and order_data.selected_color not in product.colors:
            raise HTTPException(status_code=400, detail="Invalid color")

    order = Order(
        shop_id=order_data.shop_id,
        product_id=product.id,
        customer_name=order_data.customer_name,
        customer_mobile=order_data.customer_mobile,
        delivery_address=order_data.delivery_address,
        selected_size=order_data.selected_size,
        selected_color=order_data.selected_color,
        quantity=order_data.quantity,
        unit_price=product.price,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "message": "Order created successfully",
        "order_id": order.id,
        "total_amount": order.total_amount,
        "payment_method": order.payment_method,
        "order_status": order.order_status,
    }


@app.get("/shops/{shop_id}/orders")
def get_shop_orders(
    shop_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(Order)
        .filter(Order.shop_id == shop_id)
        .order_by(Order.id.desc())
        .all()
    )


app.include_router(webhook_router)
