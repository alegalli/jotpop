from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.routers.auth import get_current_user
from app.schemas.evolution import EvolutionSummaryResponse
from app.services.auth_service import get_active_character
from app.services.evolution_service import build_evolution_summary

router = APIRouter(prefix="/evolution", tags=["evolution"])


@router.get("/summary", response_model=EvolutionSummaryResponse)
def get_evolution_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvolutionSummaryResponse:
    character = get_active_character(current_user)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active character not found")

    return EvolutionSummaryResponse(**build_evolution_summary(db, character))
