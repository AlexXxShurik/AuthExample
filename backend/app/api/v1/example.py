from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.core.permissions import require_permission
from backend.app.models.user import User

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/products")
async def get_products(
    current_user: User = Depends(require_permission("products", "read"))
):
    return {
        "products": [
            {"id": 1, "name": "Product 1", "owner_id": 1},
            {"id": 2, "name": "Product 2", "owner_id": 2},
        ]
    }


@router.get("/orders")
async def get_orders(
    current_user: User = Depends(require_permission("orders", "read"))
):
    return {
        "orders": [
            {"id": 1, "product": "Product 1", "status": "completed"},
            {"id": 2, "product": "Product 2", "status": "pending"},
        ]
    }
