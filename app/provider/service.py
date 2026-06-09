from app.database import get_db
from app.models.provider import ProviderCreate, ProviderResponse
from config import GEMINI_API_KEY
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)


def _build_embed_text(provider: ProviderCreate) -> str:
    keywords = ", ".join(provider.keywords)
    return (
        f"Name: {provider.name}. "
        f"Profession: {provider.profession}. "
        f"Domain: {provider.domain}. "
        f"Work: {provider.work_description}. "
        f"Keywords: {keywords}."
    )


async def register_provider(provider: ProviderCreate) -> ProviderResponse:
    db = get_db()

    embed_text = _build_embed_text(provider)
    result_embed = client.models.embed_content(
        model="gemini-embedding-001",
        contents=embed_text,
    )
    embedding = result_embed.embeddings[0].values

    doc = {
        "name": provider.name,
        "profession": provider.profession,
        "work_description": provider.work_description,
        "reliability_score": provider.reliability_score,
        "keywords": provider.keywords,
        "domain": provider.domain,
        "embedding": embedding,
    }

    insert_result = await db["providers"].insert_one(doc)

    return ProviderResponse(
        id=str(insert_result.inserted_id),
        name=provider.name,
        profession=provider.profession,
        domain=provider.domain,
        message="Provider registered and embedded successfully",
    )
