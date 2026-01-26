"""FastAPI router exposing Users Profiles endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.free.users.users_profiles.core.users.profiles.dto import UserProfileReadDTO, UserProfileUpdateDTO
from src.modules.free.users.users_profiles.core.users.profiles.errors import ProfileNotFoundError, ProfileValidationError
from src.modules.free.users.users_profiles.core.users.profiles.dependencies import get_user_profile_service_facade
from src.modules.free.users.users_profiles.core.users.profiles.service import UserProfileServiceFacade

router = APIRouter(prefix="/api/users/{user_id}/profile", tags=["user-profiles"])


@router.get("/", response_model=UserProfileReadDTO)
async def get_profile(
    user_id: str,
    facade: UserProfileServiceFacade = Depends(get_user_profile_service_facade),
) -> UserProfileReadDTO:
    try:
        return await facade.get_profile(user_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/", response_model=UserProfileReadDTO)
async def upsert_profile(
    user_id: str,
    payload: UserProfileUpdateDTO,
    facade: UserProfileServiceFacade = Depends(get_user_profile_service_facade),
) -> UserProfileReadDTO:
    try:
        return await facade.upsert_profile(user_id, payload)
    except ProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    user_id: str,
    facade: UserProfileServiceFacade = Depends(get_user_profile_service_facade),
) -> None:
    try:
        await facade.delete_profile(user_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


__all__ = [
    "router",
    "get_profile",
    "upsert_profile",
    "delete_profile",
]
