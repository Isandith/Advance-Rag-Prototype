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

VAGUE_FOLLOWUP_MARKER = "CLARIFY_FOLLOWUP:"
VAGUE_FOLLOWUP_QUESTION = "Can you give more details about what you're looking for?"

BLOCKED_MESSAGE = "We can't help with that here. Chat blocked — start a new chat to continue."

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
    r"\bsuicid(e|al)\b",
    r"\bkill\s+myself\b",
    r"\bself[\s-]?harm\b",
    r"\bhurt\s+myself\b",
    r"\bend\s+my\s+life\b",
    r"\bwant\s+to\s+die\b",
]


def _looks_suspicious(message: str) -> bool:
    """Cheap heuristic: true if the message looks like an attempt to extract
    credentials, system prompts, probe/attack the assistant, or otherwise
    falls outside what this provider-search assistant can help with."""
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
    f"understand, respond with exactly '{UNCLEAR_MARKER}' and nothing else — "
    "no extra words, explanation, or punctuation.\n\n"
    f"If the user's message is clearly unrelated to finding service providers "
    f"(e.g. general chit-chat unrelated to providers, requests for unrelated tasks, "
    f"or questions about topics with no connection to providers), respond with "
    f"exactly '{OFFTOPIC_MARKER}' and nothing else — no extra words, explanation, "
    "or punctuation.\n\n"
    f"If the user's message is a short follow-up (e.g. 'yes', 'is that all', "
    f"'is that the only one'): FIRST check if the provider information below "
    f"or the conversation history already answers it — if so, answer normally "
    f"using that information. ONLY if neither the provider information nor the "
    f"conversation history gives you enough to answer, respond with exactly "
    f"'{VAGUE_FOLLOWUP_MARKER}' and nothing else — no extra words, explanation, "
    "or punctuation."
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


def _looks_like_continued_gibberish(message: str) -> bool:
    """After the LLM has already said it couldn't understand the previous
    message, treat any further short message as a continuation of the same
    gibberish/spam rather than a fresh request — even if it happens to
    contain vowels in a pattern that passes _looks_like_gibberish (e.g.
    'acadsd', 'saxas'). Longer messages still go to the LLM in case the
    user typed a real request."""
    words = re.findall(r"[a-zA-Z]+", message)
    if len(words) <= 4 and len(message.strip()) <= 15:
        return True
    return _looks_like_gibberish(message)


# Short, low-content words that carry no provider-search intent on their own.
SPAM_FILLER_WORDS = {
    "why", "ok", "okay", "no", "yes", "please", "tell", "me", "huh", "what",
    "lol", "hmm", "k", "fine", "and", "so", "then", "now", "really", "sure",
    "hi", "hello", "hey", "thanks", "thank", "you",
}


def _looks_like_spam(message: str) -> bool:
    """Cheap heuristic: true if the message is short and made up only of
    low-content filler words (e.g. 'why', 'tell me please', 'ok then') —
    a continuation of spam rather than a new, on-topic request."""
    words = re.findall(r"[a-zA-Z]+", message.lower())
    if not words:
        return True
    if len(words) > 4:
        return False
    return all(word in SPAM_FILLER_WORDS for word in words)


# Phrases that ask for more detail about something already mentioned,
# rather than describing a new need (e.g. "tell me about ranil",
# "more info on Dr. Silva", "who is roshantha").
DETAIL_FOLLOWUP_PATTERNS = [
    r"\btell me (more |about )",
    r"\bmore (info|information|details?) (on|about)\b",
    r"\bwho is\b",
    r"\babout (him|her|them)\b",
]


def _looks_like_detail_followup(message: str) -> bool:
    """True if the message is asking for more detail about someone/something
    already discussed, rather than describing a new provider search."""
    lowered = message.lower()
    return any(re.search(pattern, lowered) for pattern in DETAIL_FOLLOWUP_PATTERNS)


NO_NEW_SEARCH_GUIDANCE = (
    "No relevant providers were found in the database for this message. "
    "If the user is asking a follow-up about providers already "
    "discussed earlier in this conversation, answer using that "
    "conversation history — do NOT say no providers exist or "
    "contradict what was said earlier. Otherwise, say you don't "
    "have a matching provider or ask a short clarifying question."
)


def _build_provider_context(providers: list[dict], message: str = "") -> list[SystemMessage]:
    if not providers:
        return [SystemMessage(content=NO_NEW_SEARCH_GUIDANCE)]

    entries = []
    any_keyword_match = False
    for p in providers:
        if p.get("matched_by_keyword"):
            any_keyword_match = True
            tag = ""
        else:
            tag = (
                " [uncertain match — found by semantic similarity only, "
                "may not be relevant]"
            )
        entries.append(
            f"- {p['name']} ({p['profession']}, {p['domain']}){tag}: "
            f"{p['work_description']} "
            f"Reliability: {p['reliability_score']}. "
            f"Keywords: {', '.join(p['keywords'])}."
        )

    if any_keyword_match:
        guidance = (
            "If the user's request is specific enough, use the above provider "
            "information to answer. If none of the providers are relevant, say so. "
            "If multiple providers match, briefly mention their reliability ratings "
            "so the user can choose — include lower-rated options too, don't filter "
            "them out, but let the user pick based on rating and price/preference."
        )
    elif _looks_like_spam(message):
        # Every result is a weak vector-only match and the message itself is
        # short/low-content (e.g. "yes please tell me") — these results are
        # almost certainly noise, not a real new request. Don't let the LLM
        # use them or claim no providers exist; fall back to history.
        return [SystemMessage(content=NO_NEW_SEARCH_GUIDANCE)]
    else:
        guidance = (
            "None of these providers matched the user's request by keyword — "
            "they were found by semantic similarity only and may be unrelated. "
            "Do NOT confidently recommend them. Either ask the user a short "
            "clarifying question about what they need, or say you don't have "
            "a matching provider."
        )

    text = (
        "Relevant providers from the database:\n"
        + "\n".join(entries)
        + "\n\n" + guidance
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
    unclear_count = sum(
        1 for m in history.messages
        if isinstance(m, AIMessage) and (
            m.content == FALLBACK_QUESTION
            or m.content.startswith(UNCLEAR_MARKER)
        )
    )
    # Give the user a second chance to clarify with a real LLM call before
    # falling back to the fixed question on repeat. Only switch to the
    # no-LLM cache path once the LLM has already responded "unclear" twice.
    if (
        previously_unclear
        and unclear_count >= 2
        and _looks_like_continued_gibberish(request.message)
    ):
        history.add_user_message(request.message)
        if unclear_count + 1 >= 5:
            print(f"[chat] session={session_id} source=BLOCKED (too many unclear messages)")
            history.add_ai_message(BLOCKED_MESSAGE)
            return ChatResponse(answer=BLOCKED_MESSAGE, session_id=session_id)
        print(f"[chat] session={session_id} source=CACHE (no LLM call)")
        history.add_ai_message(FALLBACK_QUESTION)
        return ChatResponse(answer=FALLBACK_QUESTION, session_id=session_id)

    # Already refused as off-topic: if the user keeps sending short,
    # low-content spam (e.g. "why", "tell me please"), repeat the fixed
    # refusal without calling the LLM. A substantive new message still
    # goes to the LLM, which can re-evaluate it fresh.
    previously_offtopic = last_ai_message is not None and (
        last_ai_message == OFFTOPIC_REFUSAL
        or last_ai_message.startswith(OFFTOPIC_MARKER)
    )
    if previously_offtopic and _looks_like_spam(request.message):
        print(f"[chat] session={session_id} source=CACHE (no LLM call)")
        history.add_user_message(request.message)
        history.add_ai_message(OFFTOPIC_REFUSAL)
        return ChatResponse(answer=OFFTOPIC_REFUSAL, session_id=session_id)

    # Already asked for more details on a vague follow-up: if the user keeps
    # sending short, low-content replies (e.g. "yes", "is that all"), repeat
    # the fixed question without calling the LLM.
    previously_vague_followup = last_ai_message is not None and (
        last_ai_message == VAGUE_FOLLOWUP_QUESTION
        or last_ai_message.startswith(VAGUE_FOLLOWUP_MARKER)
    )
    if previously_vague_followup and _looks_like_spam(request.message):
        print(f"[chat] session={session_id} source=CACHE (no LLM call)")
        history.add_user_message(request.message)
        history.add_ai_message(VAGUE_FOLLOWUP_QUESTION)
        return ChatResponse(answer=VAGUE_FOLLOWUP_QUESTION, session_id=session_id)

    # A request for more detail about someone already discussed (e.g. "tell
    # me about ranil") isn't a new provider search — answer from the existing
    # conversation history instead of running a fresh search and showing
    # provider cards again.
    if last_ai_message is not None and _looks_like_detail_followup(request.message):
        providers = []
        provider_context = _build_provider_context(providers, request.message)
    else:
        # A short confirmation/follow-up (e.g. "yes please tell me") carries no
        # search intent on its own — combine it with the assistant's previous
        # message (which likely names the profession/service in question) so the
        # search reflects what's actually being confirmed.
        if last_ai_message is not None and _looks_like_spam(request.message):
            search_query = f"{last_ai_message} {request.message}"
        else:
            search_query = request.message

        providers = await search_providers(search_query)
        provider_context = _build_provider_context(providers, request.message)

    # Persist the provider details into chat history so later follow-up
    # turns (e.g. "is he the only plumber", "why did you choose nilantha")
    # can still see who was recommended and why, even if a later search
    # doesn't find the same providers again.
    if providers:
        history.add_message(provider_context[0])

    response = await chain_with_history.ainvoke(
        {"input": request.message, "provider_context": provider_context},
        config={"configurable": {"session_id": session_id}},
    )

    answer = response.content
    if answer.startswith(UNCLEAR_MARKER):
        print(f"[chat] session={session_id} source=AI (LLM call, unclear)")
        answer = FALLBACK_QUESTION
    elif answer.startswith(OFFTOPIC_MARKER):
        print(f"[chat] session={session_id} source=AI (LLM call, off-topic)")
        answer = OFFTOPIC_REFUSAL
    elif answer.startswith(VAGUE_FOLLOWUP_MARKER):
        print(f"[chat] session={session_id} source=AI (LLM call, vague follow-up)")
        answer = VAGUE_FOLLOWUP_QUESTION
    else:
        print(f"[chat] session={session_id} source=AI (LLM call)")

    return ChatResponse(answer=answer, session_id=session_id)
