from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, Literal
from app.core.auth import verify_token
from app.services.add_library_item_service import (
    add_library_item,
    SourceNotFoundError,
)
from app.services.get_library_service import get_library
from app.services.like_library_item_service import toggle_like, ItemNotFoundError
from app.services.clone_library_item_service import (
    clone_library_course,
    clone_library_roadmap,
    PlanUpgradeRequired,
    CourseLimitExceeded,
    ItemNotFoundError as CloneItemNotFoundError,
)
from app.services.accept_share_service import TopicLimitExceeded

router = APIRouter()


# ── Request models ───────────────────────────────────────────────────────────

class AddLibraryItemRequest(BaseModel):
    user_id: str
    item_type: Literal["course", "roadmap"]
    source_id: str
    whiteboards: bool = False


class CloneLibraryItemRequest(BaseModel):
    user_id: str
    include_whiteboards: bool = False


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("")
async def add_library_item_route(
    payload: AddLibraryItemRequest,
    user=Depends(verify_token),
):
    """Add a course or roadmap to the library (any authenticated user)."""
    try:
        item = add_library_item(
            user_id=payload.user_id,
            item_type=payload.item_type,
            source_id=payload.source_id,
            whiteboards=payload.whiteboards,
        )
        return {"status": "ok", "item": item}

    except SourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("❌ ADD LIBRARY ITEM ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to add item to library")


@router.get("")
async def get_library_route(
    user_id: str = Query(...),
    item_type: Optional[str] = Query(None),   # "course" | "roadmap" | omit for both
    liked_only: bool = Query(False),
    page: int = Query(1, ge=1),
    user=Depends(verify_token),
):
    """
    Paginated library listing.
    Pro+ only — plan check is enforced here so the frontend gets a clear error.
    """
    from app.services.add_course_service import get_user_plan

    plan_id = get_user_plan(user_id)
    if plan_id == 0:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "PLAN_UPGRADE_REQUIRED",
                "message": "Library access is only available on Pro and above",
            },
        )

    try:
        result = get_library(
            user_id=user_id,
            item_type=item_type if item_type in ("course", "roadmap") else None,
            liked_only=liked_only,
            page=page,
        )
        return {"status": "ok", **result}

    except Exception as e:
        print("❌ GET LIBRARY ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch library")


@router.post("/{item_id}/like")
async def like_library_item_route(
    item_id: str,
    user_id: str = Query(...),
    user=Depends(verify_token),
):
    """Toggle like on a library item. Pro+ only."""
    from app.services.add_course_service import get_user_plan

    plan_id = get_user_plan(user_id)
    if plan_id == 0:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "PLAN_UPGRADE_REQUIRED",
                "message": "Library access is only available on Pro and above",
            },
        )

    try:
        result = toggle_like(user_id=user_id, item_id=item_id)
        return {"status": "ok", **result}

    except ItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print("❌ LIKE LIBRARY ITEM ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to toggle like")


@router.post("/{item_id}/clone")
async def clone_library_item_route(
    item_id: str,
    payload: CloneLibraryItemRequest,
    user=Depends(verify_token),
):
    """
    Clone a library item into the recipient's account.
    Works for both courses and roadmaps — item_type is resolved from the DB.
    """
    try:
        # Resolve item_type from DB so the client doesn't need to pass it
        from app.core.supabase import supabase
        item = (
            supabase.table("library_items")
            .select("item_type")
            .eq("item_id", item_id)
            .single()
            .execute()
        ).data

        if not item:
            raise HTTPException(status_code=404, detail="Library item not found")

        if item["item_type"] == "course":
            result = clone_library_course(
                item_id=item_id,
                recipient_user_id=payload.user_id,
                include_whiteboards=payload.include_whiteboards,
            )
        else:
            result = clone_library_roadmap(
                item_id=item_id,
                recipient_user_id=payload.user_id,
                include_whiteboards=payload.include_whiteboards,
            )

        return {"status": "ok", **result}

    except PlanUpgradeRequired as e:
        raise HTTPException(
            status_code=403,
            detail={"error": str(e), "error_code": "PLAN_UPGRADE_REQUIRED"},
        )
    except CourseLimitExceeded as e:
        raise HTTPException(
            status_code=403,
            detail={"error": str(e), "error_code": "COURSE_LIMIT_EXCEEDED"},
        )
    except TopicLimitExceeded as e:
        raise HTTPException(
            status_code=403,
            detail={"error": str(e), "error_code": "TOPIC_LIMIT_EXCEEDED"},
        )
    except CloneItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print("❌ CLONE LIBRARY ITEM ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to clone library item")