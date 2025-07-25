from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.schemas import Item, ItemCreate, ItemUpdate
from app.models.database import Item as ItemDB
from app.services.memory_storage import memory_storage
from app.database.connection import get_async_session
from datetime import datetime

router = APIRouter()

@router.get("/items", response_model=List[Item])
async def get_items(db: AsyncSession = Depends(get_async_session)):
    """Get all items"""
    result = await db.execute(select(ItemDB))
    items = result.scalars().all()
    return items

@router.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_async_session)):
    """Create a new item"""
    db_item = ItemDB(
        name=item.name,
        description=item.description,
        price=item.price,
        category=item.category
    )
    
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    
    # Send event to Kafka (if you still want to track item creation events)
    event_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "apppulse-backend",
        "type": "item_created",
        "data": {
            "item_id": db_item.id,
            "item_name": db_item.name,
            "category": db_item.category,
            "price": db_item.price
        }
    }
    
    return db_item

@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int, db: AsyncSession = Depends(get_async_session)):
    """Get item by ID"""
    result = await db.execute(select(ItemDB).where(ItemDB.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    return item

@router.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item_update: ItemUpdate, db: AsyncSession = Depends(get_async_session)):
    """Update an item"""
    result = await db.execute(select(ItemDB).where(ItemDB.id == item_id))
    db_item = result.scalar_one_or_none()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    # Update fields
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db_item.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_item)
    
    return db_item

@router.delete("/items/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_async_session)):
    """Delete an item"""
    result = await db.execute(select(ItemDB).where(ItemDB.id == item_id))
    db_item = result.scalar_one_or_none()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    await db.delete(db_item)
    await db.commit()
    
    return {"message": f"Item {item_id} deleted successfully"}

@router.get("/test-error")
async def test_error():
    """Test error handling and metrics"""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="This is a test error for metrics collection"
    )
