
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
    Integer,
    Computed
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from database import Base


class Shop(Base):
    __tablename__ = "shops"

    id = Column(BigInteger, primary_key=True)
    owner_name = Column(String(100), nullable=False)
    mobile_number = Column(String(15), nullable=False)
    shop_name = Column(String(150), nullable=False)
    shop_address = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    instagram_user_id = Column(String(50), unique=True, nullable=True)
    instagram_username = Column(String(100), nullable=True) 

    products = relationship(
        "Product",
        back_populates="shop",
        cascade="all, delete-orphan",
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True)
    shop_id = Column(
        BigInteger,
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
    )
    category = Column(String(100), nullable=False)
    product_name = Column(String(150), nullable=False)
    sku = Column(String(50), unique=True, nullable=False)
    image_path = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    is_configurable = Column(Boolean, default=False)
    sizes = Column(ARRAY(Text))
    colors = Column(ARRAY(Text))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    shop = relationship("Shop", back_populates="products")


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True)
    shop_id = Column(
        BigInteger,
        ForeignKey("shops.id"),
        nullable=False,
    )
    product_id = Column(
        BigInteger,
        ForeignKey("products.id"),
        nullable=False,
    )
    customer_name = Column(String(100), nullable=False)
    customer_mobile = Column(String(15), nullable=False)
    delivery_address = Column(Text, nullable=False)
    selected_size = Column(String(20))
    selected_color = Column(String(50))
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(
    Numeric(10, 2),
    Computed("quantity * unit_price", persisted=True),
    )
    payment_method = Column(String(20), nullable=False, default="COD")
    payment_status = Column(String(20), nullable=False, default="PENDING")
    order_status = Column(String(20), nullable=False, default="PLACED")
    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class ProcessedInstagramMessage(Base):
    __tablename__ = "processed_instagram_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    message_id = Column(String(255), unique=True, nullable=False)

    shop_id = Column(
        BigInteger,
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
    )

    sender_id = Column(String(50), nullable=False)

    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
    )