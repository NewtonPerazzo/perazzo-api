from fastapi import APIRouter

from app.core.plans import PLAN_CATALOG, serialize_plan

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("")
def list_plans():
    return [serialize_plan(plan_id) for plan_id in PLAN_CATALOG.keys()]
