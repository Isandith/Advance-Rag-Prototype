import re

from app.database import get_db
from app.models.provider import ProviderCreate, ProviderListItem, ProviderResponse
from config import GEMINI_API_KEY
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)

STOPWORDS = {
    "a", "an", "the", "is", "are", "i", "to", "for", "of", "in", "on",
    "with", "and", "or", "need", "want", "looking", "find", "me", "my",
    "who", "can", "you", "please", "help", "some", "good",
}


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


async def list_providers() -> list[ProviderListItem]:
    db = get_db()

    cursor = db["providers"].find({}, {"embedding": 0})
    providers = []
    async for doc in cursor:
        providers.append(
            ProviderListItem(
                id=str(doc["_id"]),
                name=doc["name"],
                profession=doc["profession"],
                work_description=doc["work_description"],
                reliability_score=doc["reliability_score"],
                keywords=doc["keywords"],
                domain=doc["domain"],
            )
        )

    return providers


async def search_providers(query: str, limit: int = 5) -> list[dict]:
    """Hybrid search over providers: vector similarity on the embedding
    plus keyword matching on name/profession/domain/keywords/work_description.
    Returns plain dicts (no embedding field) ordered by relevance.
    """
    db = get_db()

    result_embed = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
    )
    query_embedding = result_embed.embeddings[0].values

    vector_pipeline = [
        {
            "$vectorSearch": {
                "index": "provider_vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": limit * 10,
                "limit": limit,
            }
        },
        {"$set": {"score": {"$meta": "vectorSearchScore"}}},
        {"$project": {"embedding": 0}},
    ]

    words = [
        re.escape(w)
        for w in re.findall(r"\w+", query.lower())
        if w not in STOPWORDS and len(w) > 2
    ]

    vector_results = []
    try:
        vector_results = await db["providers"].aggregate(vector_pipeline).to_list(length=limit)
    except Exception:
        vector_results = []

    keyword_results = []
    if words:
        keyword_filter = {
            "$or": [
                {"name": {"$regex": word, "$options": "i"}}
                for word in words
            ] + [
                {"profession": {"$regex": word, "$options": "i"}}
                for word in words
            ] + [
                {"domain": {"$regex": word, "$options": "i"}}
                for word in words
            ] + [
                {"work_description": {"$regex": word, "$options": "i"}}
                for word in words
            ] + [
                {"keywords": {"$regex": word, "$options": "i"}}
                for word in words
            ]
        }
        candidates = await db["providers"].find(
            keyword_filter, {"embedding": 0}
        ).to_list(length=None)

        def _relevance(doc: dict) -> int:
            profession = doc.get("profession", "").lower()
            keywords_text = " ".join(doc.get("keywords", [])).lower()
            work_description = doc.get("work_description", "").lower()
            name = doc.get("name", "").lower()
            domain = doc.get("domain", "").lower()
            score = 0
            for word in words:
                if re.search(word, profession) or re.search(word, keywords_text):
                    score += 3
                elif re.search(word, work_description) or re.search(word, name):
                    score += 2
                elif re.search(word, domain):
                    score += 1
            return score

        candidates.sort(key=_relevance, reverse=True)
        keyword_results = candidates[:limit]

    keyword_ids = {str(doc["_id"]) for doc in keyword_results}

    merged: dict[str, dict] = {}
    for doc in vector_results + keyword_results:
        merged[str(doc["_id"])] = doc

    providers = []
    for doc_id, doc in merged.items():
        doc["_id"] = doc_id
        doc["matched_by_keyword"] = doc_id in keyword_ids
        providers.append(doc)

    return providers[:limit]
