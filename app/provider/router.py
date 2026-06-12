from fastapi import APIRouter
from app.models.provider import ProviderCreate, ProviderListItem, ProviderResponse
from app.provider.service import list_providers, register_provider

router = APIRouter(prefix="/providers", tags=["providers"])


@router.post("/", response_model=ProviderResponse)
async def create_provider(provider: ProviderCreate):
    return await register_provider(provider)


@router.get("/", response_model=list[ProviderListItem])
async def get_providers():
    return await list_providers()
