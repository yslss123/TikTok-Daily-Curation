import json
import logging
import os
from urllib.request import Request, urlopen

CATEGORIES = {"funny", "beauty", "creative", "curiosity"}

KEYWORDS = {
    "funny": {
        "funny", "comedy", "hilarious", "laugh", "meme", "prank", "joke", "lol", "fails",
        "skit", "搞笑", "笑", "沙雕", "段子", "恶搞", "整蛊",
    },
    "beauty": {
        "beauty", "makeup", "skincare", "fashion", "ootd", "hairstyle", "glowup",
        "aesthetic", "make over", "颜值", "美妆", "穿搭", "变装", "化妆", "护肤",
    },
    "creative": {
        "creative", "art", "diy", "craft", "design", "animation", "satisfying",
        "lifehack", "tutorial", "手工", "创意", "制作", "技巧", "特效", "发明",
    },
    "curiosity": {
        "weird", "strange", "amazing", "unbelievable", "facts", "mystery", "odd",
        "unusual", "discovery", "奇闻", "冷知识", "罕见", "神奇", "震惊", "科普",
    },
}


class KeywordClassifier:
    """Deterministic metadata classifier; it does not inspect video pixels."""

    name = "keyword"

    def classify(self, candidate) -> tuple[str, float]:
        text = " ".join([
            candidate.title, candidate.description, " ".join(candidate.hashtags)
        ]).lower()
        scores = {
            category: sum(1 for keyword in words if keyword in text)
            for category, words in KEYWORDS.items()
        }
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            total = sum(scores.values())
            confidence = min(0.95, 0.55 + scores[best] / max(total, 1) * 0.35)
            return best, round(confidence, 3)
        if candidate.category in CATEGORIES:
            return candidate.category, 0.55
        return "uncategorized", 0.0


class OpenAICompatibleClassifier:
    """Optional text-metadata classifier for OpenAI-compatible chat completions."""

    name = "ai_metadata"

    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 25):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def classify(self, candidate) -> tuple[str, float]:
        endpoint = self.base_url if self.base_url.endswith("/chat/completions") else f"{self.base_url}/chat/completions"
        prompt = (
            "Classify this short-video metadata into exactly one category: funny, beauty, "
            "creative, curiosity, or uncategorized. Use only the supplied title, description "
            "and hashtags; do not infer a person's identity or sensitive traits. Return JSON "
            "only: {\"category\": string, \"confidence\": number between 0 and 1}.\n"
            f"Title: {candidate.title}\nDescription: {candidate.description}\n"
            f"Hashtags: {', '.join(candidate.hashtags)}"
        )
        body = json.dumps({
            "model": self.model,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        request = Request(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = json.loads(content)
        category = str(result.get("category", "uncategorized")).lower()
        if category not in CATEGORIES and category != "uncategorized":
            category = "uncategorized"
        confidence = max(0.0, min(1.0, float(result.get("confidence", 0.0))))
        return category, confidence


class FallbackClassifier:
    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback
        self.name = getattr(primary, "name", "primary")

    def classify(self, candidate) -> tuple[str, float]:
        try:
            return self.primary.classify(candidate)
        except Exception as exc:
            logging.warning("AI metadata classification failed; using keyword fallback: %s", exc)
            category, confidence = self.fallback.classify(candidate)
            return category, confidence


def build_classifier():
    api_key = os.getenv("AI_API_KEY", "").strip()
    if not api_key:
        return KeywordClassifier()
    return FallbackClassifier(
        OpenAICompatibleClassifier(
            api_key=api_key,
            base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("AI_MODEL", "gpt-4o-mini"),
        ),
        KeywordClassifier(),
    )
