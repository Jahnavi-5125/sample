from http.client import HTTPException
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from src.backend.db import mongodb
from src.backend.core.api_limit import apiSecurityFree
from src.backend.models.app_io_schemas import Onboarding, OnboardingRequest
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

router = APIRouter()

@router.patch("/user")
async def update_user(user: apiSecurityFree, request: mongodb.UpdateUserRequest):

    for key,value in request.model_dump().items() :
        if value :
            user._set_attr(key,value)
        
    await user.save()
    return user


@router.get("/personalization_info")
async def get_user_personalization(user: apiSecurityFree):
    personalization = await mongodb.get_personalization(user.id.__str__())
    if not personalization:
        raise HTTPException(status_code=200, detail="Please take a moment to set up your preferences to enhance your experience.")
    return personalization

@router.post("/personalization")
async def update_user_personalization(user: apiSecurityFree, request: mongodb.PersonalizationRequest):
    updated = await mongodb.create_or_update_personalization(user.id.__str__(), request.dict(exclude_unset=True))
    return updated

@router.delete("/user/{user_id}")
async def delete_user_endpoint(user_id: str):
    try:
        # Use the cascading delete service function
        result = await mongodb.delete_user(user_id)
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404 User not found)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error occurred while deleting user: {str(e)}"
        )
     
@router.get("/is_new_user")
async def is_new_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return await mongodb.is_new_user_token(token)
@router.post("/onboarding", response_model=Onboarding)
async def update_onboarding(user: apiSecurityFree, request: OnboardingRequest):
    try:
        updated = await mongodb.create_or_update_onboarding(user.id.__str__(), request.dict(exclude_unset=True))
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/get_user_info")
async def user_by_id(user: apiSecurityFree):
    return user.to_dict()
