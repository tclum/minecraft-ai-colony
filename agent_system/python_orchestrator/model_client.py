import requests
from .config import (
    MODEL_API_KEY,
    MODEL_BASE_URL,
    REVIEW_PROVIDER,
    REVIEW_API_KEY
)

def call_model(system_prompt, user_prompt, model_name, json_mode=False, provider="openai"):
    if provider == "openai":
        url = MODEL_BASE_URL.rstrip("/") + "/chat/completions"

        headers = {
            "Authorization": f"Bearer {MODEL_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if not response.ok:
            raise RuntimeError(f"OpenAI error {response.status_code}: {response.text}")

        return response.json()["choices"][0]["message"]["content"]

    elif provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"

        headers = {
            "x-api-key": REVIEW_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        prompt = f"{system_prompt}\n\n{user_prompt}"

        payload = {
            "model": model_name,
            "max_tokens": 2000,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if not response.ok:
            raise RuntimeError(f"Claude error {response.status_code}: {response.text}")

        return response.json()["content"][0]["text"]

    else:
        raise ValueError(f"Unknown provider: {provider}")