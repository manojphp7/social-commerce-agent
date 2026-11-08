
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class OrderCreate(BaseModel):
    shop_id: int
    product_id: int
    customer_name: str = Field(min_length=1, max_length=100)
    customer_mobile: str = Field(min_length=10, max_length=15)
    delivery_address: str = Field(min_length=5)
    selected_size: Optional[str] = None
    selected_color: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
