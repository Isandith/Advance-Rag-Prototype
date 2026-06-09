from fastapi import APIRouter
from app.models.provider import ProviderCreate, ProviderResponse
from app.provider.service import register_provider

router = APIRouter(prefix="/providers", tags=["providers"])


@router.post("/", response_model=ProviderResponse)
async def create_provider(provider: ProviderCreate):
    return await register_provider(provider)
