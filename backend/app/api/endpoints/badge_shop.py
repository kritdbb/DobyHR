"""
Badge Shop API: browse and purchase badges with Gold, Mana, or Thank You Cards.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.user import User
from app.models.badge import Badge, UserBadge
from app.models.badge_shop import BadgeShopItem, BadgeShopPurchase
from app.models.social import ThankYouCard
from app.models.reward import CoinLog
from app.api import deps

router = APIRouter(prefix="/api/badge-shop", tags=["Badge Shop"])


# ── Schemas ──────────────────────────────────────────────

class ShopItemCreate(BaseModel):
    badge_id: int
    price_type: str          # gold | mana | thankyou
    price_amount: int
    stock: Optional[int] = None

class ShopItemUpdate(BaseModel):
    badge_id: Optional[int] = None
    price_type: Optional[str] = None
    price_amount: Optional[int] = None
    stock: Optional[int] = None
    active: Optional[bool] = None


# ── Helpers ──────────────────────────────────────────────

VALID_PRICE_TYPES = {"gold", "mana", "thankyou"}


def _thank_you_balance(user_id: int, db: Session) -> int:
    """Thank You Cards received (all-time) minus cards spent on purchases."""
    received = db.query(func.count(ThankYouCard.id)).filter(
        ThankYouCard.recipient_id == user_id,
    ).scalar() or 0

    spent = db.query(func.coalesce(func.sum(BadgeShopPurchase.price_amount), 0)).filter(
        BadgeShopPurchase.user_id == user_id,
        BadgeShopPurchase.price_type == "thankyou",
    ).scalar() or 0

    return max(received - spent, 0)


def _item_to_dict(item: BadgeShopItem, badge: Badge, sold: int = 0):
    return {
        "id": item.id,
        "badge_id": item.badge_id,
        "badge_name": badge.name if badge else "Unknown",
        "badge_description": badge.description if badge else "",
        "badge_image": badge.image if badge else None,
        "badge_stat_str": badge.stat_str if badge else 0,
        "badge_stat_def": badge.stat_def if badge else 0,
        "badge_stat_luk": badge.stat_luk if badge else 0,
        "price_type": item.price_type,
        "price_amount": item.price_amount,
        "stock": item.stock,
        "sold": sold,
        "active": item.active,
    }


# ═══════════════════════════════════════════════════════════
# STAFF ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/catalog")
def get_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """List active shop items with badge details and user balances."""
    items = db.query(BadgeShopItem).filter(BadgeShopItem.active == True).all()

    # Get user's existing badges
    owned_badge_ids = set(
        r[0] for r in db.query(UserBadge.badge_id).filter(UserBadge.user_id == current_user.id).all()
    )

    catalog = []
    for item in items:
        badge = db.query(Badge).filter(Badge.id == item.badge_id).first()
        sold = db.query(func.count(BadgeShopPurchase.id)).filter(
            BadgeShopPurchase.shop_item_id == item.id,
        ).scalar() or 0

        # Skip if out of stock
        if item.stock is not None and sold >= item.stock:
            continue

        d = _item_to_dict(item, badge, sold)
        d["owned"] = item.badge_id in owned_badge_ids
        d["remaining"] = (item.stock - sold) if item.stock is not None else None
        catalog.append(d)

    return {
        "items": catalog,
        "balances": {
            "gold": current_user.coins or 0,
            "mana": current_user.angel_coins or 0,
            "thankyou": _thank_you_balance(current_user.id, db),
        },
    }


@router.post("/buy/{item_id}")
def buy_badge(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Purchase a badge from the shop."""
    item = db.query(BadgeShopItem).filter(
        BadgeShopItem.id == item_id,
        BadgeShopItem.active == True,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or inactive")

    badge = db.query(Badge).filter(Badge.id == item.badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    # Check duplicate ownership
    existing = db.query(UserBadge).filter(
        UserBadge.user_id == current_user.id,
        UserBadge.badge_id == item.badge_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already own this badge!")

    # Check stock
    if item.stock is not None:
        sold = db.query(func.count(BadgeShopPurchase.id)).filter(
            BadgeShopPurchase.shop_item_id == item.id,
        ).scalar() or 0
        if sold >= item.stock:
            raise HTTPException(status_code=400, detail="This badge is sold out!")

    # ── Deduct currency ──
    price = item.price_amount

    if item.price_type == "gold":
        if (current_user.coins or 0) < price:
            raise HTTPException(status_code=400, detail=f"Not enough Gold! Need {price}, have {current_user.coins or 0}")
        current_user.coins -= price
        log = CoinLog(
            user_id=current_user.id,
            amount=-price,
            reason=f"🏪 Badge Shop — purchased \"{badge.name}\"",
            created_by="Badge Shop",
        )
        db.add(log)

    elif item.price_type == "mana":
        if (current_user.angel_coins or 0) < price:
            raise HTTPException(status_code=400, detail=f"Not enough Mana! Need {price}, have {current_user.angel_coins or 0}")
        current_user.angel_coins -= price

    elif item.price_type == "thankyou":
        balance = _thank_you_balance(current_user.id, db)
        if balance < price:
            raise HTTPException(status_code=400, detail=f"Not enough Thank You Cards! Need {price}, have {balance}")
        # Thank You balance is virtual (received - spent), purchase record handles deduction

    else:
        raise HTTPException(status_code=400, detail="Invalid price type")

    # ── Award badge ──
    user_badge = UserBadge(
        user_id=current_user.id,
        badge_id=item.badge_id,
        awarded_by="Badge Shop",
    )
    db.add(user_badge)

    # ── Log purchase ──
    purchase = BadgeShopPurchase(
        user_id=current_user.id,
        shop_item_id=item.id,
        price_type=item.price_type,
        price_amount=price,
    )
    db.add(purchase)

    db.commit()

    return {
        "message": f"🏪 Successfully purchased \"{badge.name}\"!",
        "badge_name": badge.name,
        "badge_image": badge.image,
        "price_type": item.price_type,
        "price_amount": price,
        "balances": {
            "gold": current_user.coins or 0,
            "mana": current_user.angel_coins or 0,
            "thankyou": _thank_you_balance(current_user.id, db),
        },
    }


@router.get("/my-purchases")
def my_purchases(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get current user's purchase history."""
    purchases = (
        db.query(BadgeShopPurchase)
        .filter(BadgeShopPurchase.user_id == current_user.id)
        .order_by(BadgeShopPurchase.purchased_at.desc())
        .all()
    )
    result = []
    for p in purchases:
        item = db.query(BadgeShopItem).filter(BadgeShopItem.id == p.shop_item_id).first()
        badge = db.query(Badge).filter(Badge.id == item.badge_id).first() if item else None
        result.append({
            "id": p.id,
            "badge_name": badge.name if badge else "Unknown",
            "badge_image": badge.image if badge else None,
            "price_type": p.price_type,
            "price_amount": p.price_amount,
            "purchased_at": p.purchased_at.isoformat() if p.purchased_at else None,
        })
    return result


# ═══════════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/admin/items")
def admin_list_items(
    db: Session = Depends(get_db),
    admin: User = Depends(deps.get_current_gm_or_above),
):
    """List all shop items (including inactive)."""
    items = db.query(BadgeShopItem).order_by(BadgeShopItem.created_at.desc()).all()
    result = []
    for item in items:
        badge = db.query(Badge).filter(Badge.id == item.badge_id).first()
        sold = db.query(func.count(BadgeShopPurchase.id)).filter(
            BadgeShopPurchase.shop_item_id == item.id,
        ).scalar() or 0
        result.append(_item_to_dict(item, badge, sold))
    return result


@router.post("/admin/items")
def admin_create_item(
    req: ShopItemCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(deps.get_current_gm_or_above),
):
    """Create a new shop item."""
    if req.price_type not in VALID_PRICE_TYPES:
        raise HTTPException(status_code=400, detail=f"price_type must be one of: {VALID_PRICE_TYPES}")

    badge = db.query(Badge).filter(Badge.id == req.badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    item = BadgeShopItem(
        badge_id=req.badge_id,
        price_type=req.price_type,
        price_amount=req.price_amount,
        stock=req.stock,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return _item_to_dict(item, badge)


@router.put("/admin/items/{item_id}")
def admin_update_item(
    item_id: int,
    req: ShopItemUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(deps.get_current_gm_or_above),
):
    """Update a shop item."""
    item = db.query(BadgeShopItem).filter(BadgeShopItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if req.badge_id is not None:
        badge = db.query(Badge).filter(Badge.id == req.badge_id).first()
        if not badge:
            raise HTTPException(status_code=404, detail="Badge not found")
        item.badge_id = req.badge_id
    if req.price_type is not None:
        if req.price_type not in VALID_PRICE_TYPES:
            raise HTTPException(status_code=400, detail=f"price_type must be one of: {VALID_PRICE_TYPES}")
        item.price_type = req.price_type
    if req.price_amount is not None:
        item.price_amount = req.price_amount
    if req.stock is not None:
        item.stock = req.stock
    if req.active is not None:
        item.active = req.active

    db.commit()
    db.refresh(item)

    badge = db.query(Badge).filter(Badge.id == item.badge_id).first()
    return _item_to_dict(item, badge)


@router.delete("/admin/items/{item_id}")
def admin_delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(deps.get_current_gm_or_above),
):
    """Delete a shop item."""
    item = db.query(BadgeShopItem).filter(BadgeShopItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted"}
