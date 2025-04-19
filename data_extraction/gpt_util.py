import openai
import time
import tiktoken

# Token tracking for rate limiting
token_timestamps = []

# Model constraints
GPT_4o_mini = {
    "MODEL_NAME": "gpt-4o-mini",
    "RATE_LIMIT_WINDOW": 60,  # seconds
    "MAX_CONTEXT_TOKENS": 128000,
    "TOKEN_LIMIT_PER_MINUTE": 200000,
}

GPT_SUMMARY_MODEL = "chatgpt-4o-latest"
SAFE_COMPLETION_TOKENS = 500  # Leave space for response

# Initialize tokenizer
encoder = tiktoken.encoding_for_model(GPT_4o_mini["MODEL_NAME"])


def num_tokens_from_string(
    string: str, model_name: str = GPT_4o_mini["MODEL_NAME"]
) -> int:
    """Returns num of tokens in a string(usually prompt) as per model type"""
    encoding = tiktoken.encoding_for_model(model_name)
    return len(encoding.encode(string))


def enforce_rate_limit(tokens_needed):
    """Ensures token usage stays within the tokens per minute limit."""
    global token_timestamps
    now = time.time()
    token_timestamps = [
        (t, tok)
        for (t, tok) in token_timestamps
        if (now - t) < GPT_4o_mini["RATE_LIMIT_WINDOW"]
    ]

    current_usage = sum(tok for _, tok in token_timestamps)

    while current_usage + tokens_needed > GPT_4o_mini["TOKEN_LIMIT_PER_MINUTE"]:
        time.sleep(1)
        now = time.time()
        token_timestamps = [
            (t, tok)
            for (t, tok) in token_timestamps
            if (now - t) < GPT_4o_mini["RATE_LIMIT_WINDOW"]
        ]
        current_usage = sum(tok for _, tok in token_timestamps)

    token_timestamps.append((time.time(), tokens_needed))


def ask_gpt(context: str, prompt: str):
    """Calls OpenAI GPT with built-in rate limiting."""

    # Token estimation
    tokens_for_prompt = num_tokens_from_string(prompt)
    tokens_for_context = num_tokens_from_string(context)

    total_tokens_needed = (
        tokens_for_prompt + tokens_for_context + SAFE_COMPLETION_TOKENS
    )

    # ask directly if total_tokens_needed > MAX_CONTEXT_TOKENS
    if total_tokens_needed > GPT_4o_mini["MAX_CONTEXT_TOKENS"]:
        raise ValueError("Total tokens needed exceed the maximum context tokens limit.")

    # else send request with context
    # Ensure rate limit is not exceeded
    enforce_rate_limit(total_tokens_needed)

    # Send API request
    response = openai.chat.completions.create(
        model=GPT_4o_mini["MODEL_NAME"],
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": context},
        ],
        max_tokens=SAFE_COMPLETION_TOKENS,
    )

    return response.choices[0].message.content
