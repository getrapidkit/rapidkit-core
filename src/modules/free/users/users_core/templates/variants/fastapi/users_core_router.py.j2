"""FastAPI router exposing Users Core endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.free.users.users_core.core.users.dto import (
    UserCreateDTO,
    UserDTO,
    UserUpdateDTO,
)
from src.modules.free.users.users_core.core.users.errors import (
    UserEmailConflictError,
    UserNotFoundError,
    UserRegistrationDisabledError,
)
from src.modules.free.users.users_core.core.users.dependencies import get_users_service_facade
from src.modules.free.users.users_core.core.users.service import UsersServiceFacade

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=list[UserDTO])
async def list_users(
    limit: int | None = None,
    offset: int = 0,
    facade: UsersServiceFacade = Depends(get_users_service_facade),
) -> list[UserDTO]:
    """List users with optional pagination."""

    results = await facade.list_users(limit=limit, offset=offset)
    return list(results)


@router.get("/{user_id}", response_model=UserDTO)
async def get_user(
    user_id: str,
    facade: UsersServiceFacade = Depends(get_users_service_facade),
) -> UserDTO:
    try:
        return await facade.get_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/", response_model=UserDTO, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateDTO,
    facade: UsersServiceFacade = Depends(get_users_service_facade),
) -> UserDTO:
    try:
        return await facade.create_user(payload)
    except UserRegistrationDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except UserEmailConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{user_id}", response_model=UserDTO)
async def update_user(
    user_id: str,
    payload: UserUpdateDTO,
    facade: UsersServiceFacade = Depends(get_users_service_facade),
) -> UserDTO:
    try:
        return await facade.update_user(user_id, payload)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    facade: UsersServiceFacade = Depends(get_users_service_facade),
) -> None:
    try:
        await facade.delete_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


__all__ = [
    "router",
    "list_users",
    "get_user",
    "create_user",
    "update_user",
    "delete_user",
]
