import httpx

from frontend.config import CHAT_URL, HEALTH_URL


def check_backend() -> bool:
    try:
        r = httpx.get(HEALTH_URL, timeout=2.0)
        return r.status_code == 200
    except httpx.HTTPError:
        return False


def stream_from_backend(question: str):
    with httpx.Client(timeout=None) as client:
        with client.stream(
            "POST",
            CHAT_URL,
            json={"question": question},
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_text():
                if chunk:
                    yield chunk
