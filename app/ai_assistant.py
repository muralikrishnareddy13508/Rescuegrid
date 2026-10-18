"""Optional OpenAI-compatible chat adapter; gracefully reports when not configured."""
import json
import os
import urllib.error
import urllib.request


def generate_answer(question: str) -> dict:
    """Call a configured OpenAI-compatible endpoint, or return a transparent fallback."""
    base = os.getenv("RESCUEGRID_LLM_BASE_URL", "").strip().rstrip("/")
    model = os.getenv("RESCUEGRID_LLM_MODEL", "").strip()
    key = os.getenv("RESCUEGRID_LLM_API_KEY", "").strip()
    if not base or not model:
        return {
            "answer": "Generative AI is not configured on this server yet. I can still explain the platform's rules: food-safety eligibility is determined by explicit checks and human review; AI urgency estimates never override safety rules; only completed handoffs count as confirmed rescued food.",
            "mode": "fallback",
            "generated": False,
            "configuration_hint": "Set RESCUEGRID_LLM_BASE_URL and RESCUEGRID_LLM_MODEL (and API key if required) to enable an OpenAI-compatible chat endpoint.",
        }
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "You are the RESCUEGRID food-rescue assistant. Never make food-safety decisions. Explain that explicit safety checks and human review govern eligibility. Distinguish predictions from confirmed facts and only call completed handoffs confirmed rescued food. Do not claim partnerships or invent data."},
            {"role": "user", "content": question[:2000]},
        ],
        "temperature": 0.2,
    }).encode()
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    request = urllib.request.Request(base + "/chat/completions", data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode())
        answer = result["choices"][0]["message"]["content"]
        return {"answer": str(answer), "mode": "configured-model", "generated": True}
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        return {"answer": "The configured AI service could not be reached. Please try again later. The platform's safety rules remain independent of AI.", "mode": "service-unavailable", "generated": False, "error_type": type(exc).__name__}
