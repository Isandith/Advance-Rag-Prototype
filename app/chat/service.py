import re
import uuid

from app.models.chat import ChatRequest, ChatResponse
from app.provider.service import search_providers
from config import GEMINI_API_KEY, GEMINI_MODEL, MONGODB_URI, DB_NAME
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory


llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GEMINI_API_KEY,
)

UNCLEAR_MARKER = "CLARIFY_UNCLEAR:"
FALLBACK_QUESTION = "Didn't understand. What provider or service are you looking for?"

OFFTOPIC_MARKER = "REFUSE_OFFTOPIC:"
OFFTOPIC_REFUSAL = "I can only help find service providers."

BLOCKED_MESSAGE = "Chat blocked. Start a new chat to continue."

SUSPICIOUS_PATTERNS = [
    r"\bpassword(s)?\b",
    r"\badmin(istrator)?\s*(password|credentials|access|login)\b",
    r"\bcredentials?\b",
    r"\bapi[\s_-]?keys?\b",
    r"\bsecret[\s_-]?keys?\b",
    r"\baccess\s*token(s)?\b",
    r"\bprivate\s*key(s)?\b",
    r"\bignore\s+(all\s+)?(previous|prior|above)\s+instructions\b",
    r"\bsystem\s*prompt\b",
    r"\byour\s+(instructions|prompt|configuration)\b",
    r"\bsudo\b",
    r"\bdrop\s+table\b",
    r"\bsql\s*injection\b",
]


def _looks_suspicious(message: str) -> bool:
    """Cheap heuristic: true if the message looks like an attempt to extract
    credentials, system prompts, or otherwise probe/attack the assistant."""
    lowered = message.lower()
    return any(re.search(pattern, lowered) for pattern in SUSPICIOUS_PATTERNS)


SYSTEM_PROMPT = (
    "You are an assistant that helps users find service providers from a database. "
    "Keep replies short and direct — answer in 1-3 sentences, no filler or "
    "unnecessary pleasantries.\n\n"
    "If the user's request is vague or missing details needed to find the right "
    "provider (such as what kind of service, profession, domain, or specific need "
    "they're looking for), do NOT guess or search blindly — ask a short clarifying "
    "question instead. Once the request is clear, use the provider information "
    "given to you to answer.\n\n"
    f"If the user's message is gibberish, nonsensical, or otherwise impossible to "
    f"understand, respond with exactly '{UNCLEAR_MARKER}' followed by a short, "
    "friendly request for them to rephrase or explain what they need.\n\n"
    f"If the user's message is clearly unrelated to finding service providers "
    f"(e.g. general chit-chat unrelated to providers, requests for unrelated tasks, "
    f"or questions about topics with no connection to providers), respond with "
    f"exactly '{OFFTOPIC_MARKER}' followed by a short, polite refusal explaining "
    "you can only help with finding service providers."
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        MessagesPlaceholder(variable_name="provider_context"),
        ("human", "{input}"),
    ]
)

chain = prompt | llm


def _get_session_history(session_id: str) -> MongoDBChatMessageHistory:
    return MongoDBChatMessageHistory(
        connection_string=MONGODB_URI,
        session_id=session_id,
        database_name=DB_NAME,
        collection_name="chat_history",
    )


chain_with_history = RunnableWithMessageHistory(
    chain,
    _get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)


def _looks_like_gibberish(message: str) -> bool:
    """Cheap heuristic: true if the message has no word that looks like
    real language (e.g. random keyboard mashing like 'asdssafa' or
    'sdwfdggg' — long consonant runs, no vowels)."""
    words = re.findall(r"[a-zA-Z]+", message)
    for word in words:
        if len(word) < 3:
            continue
        vowels = sum(1 for c in word.lower() if c in "aeiou")
        if vowels == 0:
            continue
        if re.search(r"[^aeiou]{4,}", word.lower()):
            continue
        return False
    return True


def _build_provider_context(providers: list[dict]) -> list[SystemMessage]:
    if not providers:
        return []

    entries = []
    for p in providers:
        entries.append(
            f"- {p['name']} ({p['profession']}, {p['domain']}): "
            f"{p['work_description']} "
            f"Reliability: {p['reliability_score']}. "
            f"Keywords: {', '.join(p['keywords'])}."
        )

    text = (
        "Relevant providers from the database:\n"
        + "\n".join(entries)
        + "\n\nIf the user's request is specific enough, use the above provider "
        "information to answer. If none of the providers are relevant, say so."
    )

    return [SystemMessage(content=text)]


async def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    history = _get_session_history(session_id)

    last_ai_message = next(
        (m.content for m in reversed(history.messages) if isinstance(m, AIMessage)),
        None,
    )

    # Chat is permanently blocked: no further messages are processed, by the
    # LLM or otherwise. The user must start a new chat (new session_id).
    if last_ai_message == BLOCKED_MESSAGE:
        print(f"[chat] session={session_id} source=BLOCKED (chat locked)")
        return ChatResponse(answer=BLOCKED_MESSAGE, session_id=session_id)

    # Suspicious request (e.g. probing for credentials, prompt injection):
    # refuse immediately and permanently block this session.
    if _looks_suspicious(request.message):
        print(f"[chat] session={session_id} source=BLOCKED (suspicious input)")
        history.add_user_message(request.message)
        history.add_ai_message(BLOCKED_MESSAGE)
        return ChatResponse(answer=BLOCKED_MESSAGE, session_id=session_id)

    # Already in fallback "spam mode": if the new message is still gibberish,
    # repeat the fixed fallback question without calling the LLM.
    previously_unclear = last_ai_message is not None and (
        last_ai_message == FALLBACK_QUESTION
        or last_ai_message.startswith(UNCLEAR_MARKER)
    )
    if previously_unclear and _looks_like_gibberish(request.message):
        print(f"[chat] session={session_id} source=CACHE (no LLM call)")
        history.add_user_message(request.message)
        history.add_ai_message(FALLBACK_QUESTION)
        return ChatResponse(answer=FALLBACK_QUESTION, session_id=session_id)

    # Already refused as off-topic: if the user keeps going, repeat the
    # fixed refusal without calling the LLM.
    previously_offtopic = last_ai_message is not None and (
        last_ai_message == OFFTOPIC_REFUSAL
        or last_ai_message.startswith(OFFTOPIC_MARKER)
    )
    if previously_offtopic:
        print(f"[chat] session={session_id} source=CACHE (no LLM call)")
        history.add_user_message(request.message)
        history.add_ai_message(OFFTOPIC_REFUSAL)
        return ChatResponse(answer=OFFTOPIC_REFUSAL, session_id=session_id)

    providers = await search_providers(request.message)
    provider_context = _build_provider_context(providers)

    response = await chain_with_history.ainvoke(
        {"input": request.message, "provider_context": provider_context},
        config={"configurable": {"session_id": session_id}},
    )

    answer = response.content
    if answer.startswith(UNCLEAR_MARKER):
        if previously_unclear:
            print(f"[chat] session={session_id} source=CACHE (LLM said unclear again)")
            answer = FALLBACK_QUESTION
        else:
            print(f"[chat] session={session_id} source=AI (LLM call)")
            answer = answer[len(UNCLEAR_MARKER):].strip()
    elif answer.startswith(OFFTOPIC_MARKER):
        print(f"[chat] session={session_id} source=AI (LLM call)")
        answer = answer[len(OFFTOPIC_MARKER):].strip()
    else:
        print(f"[chat] session={session_id} source=AI (LLM call)")

    return ChatResponse(answer=answer, session_id=session_id)
