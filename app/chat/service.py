from app.database import get_db
from app.models.chat import ChatRequest, ChatResponse
from config import GEMINI_API_KEY, GEMINI_MODEL
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage


llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GEMINI_API_KEY,
)


async def chat(request: ChatRequest) -> ChatResponse:
    response = await llm.ainvoke([HumanMessage(content=request.message)])
    return ChatResponse(answer=response.content)
