"""
HireLens AI — Resume Bullet Point Improver
Uses Anthropic API directly (not CrewAI) for fast, targeted rewrites.
Falls back to heuristic rewrites when no API key is present.
"""

from __future__ import annotations
import os
import re
import json
from typing import List
from dataclasses import dataclass


@dataclass
class BulletImprovement:
    original: str
    improved: str
    changes: List[str]          # short explanations of what changed
    impact_delta: int           # estimated score improvement (+points)


_WEAK_VERBS = {
    "helped",  "assisted", "worked on", "participated in",
    "contributed to", "was involved in", "supported", "did",
    "handled", "managed", "performed", "did work on",
}

_STRONG_VERB_MAP = {
    "helped":            "Supported",
    "assisted":          "Enabled",
    "worked on":         "Delivered",
    "participated in":   "Contributed to",
    "contributed to":    "Drove",
    "was involved in":   "Executed",
    "supported":         "Facilitated",
    "did":               "Executed",
    "handled":           "Owned",
    "managed":           "Led",
    "performed":         "Executed",
}

_METRIC_SUGGESTIONS = [
    "Add a % improvement (e.g., reduced latency by 40%)",
    "Include scale (e.g., serving 50K daily users)",
    "Add time saved (e.g., cut deploy time from 2hr to 15min)",
    "Mention $ impact (e.g., $200K annual cost savings)",
]


def _heuristic_improve(bullet: str) -> BulletImprovement:
    """Simple rule-based improvement when no API key available."""
    original = bullet.strip()
    improved  = original
    changes   = []
    delta     = 0

    # 1. Replace weak verb at start
    lower = original.lower()
    for weak, strong in _STRONG_VERB_MAP.items():
        if lower.startswith(weak):
            improved = strong + original[len(weak):]
            changes.append(f"Replaced weak verb '{weak}' → '{strong}'")
            delta += 8
            break

    # 2. Check for metrics — if none, add suggestion placeholder
    has_metric = bool(re.search(
        r'\d+\s*(%|x|ms|k\b|m\b|\$|users?|customers?|hrs?)', improved, re.IGNORECASE
    ))
    if not has_metric:
        # Add a placeholder suggestion
        improved = improved.rstrip(".")
        improved += " — [ADD METRIC: e.g., reducing X by Y%]"
        changes.append("No quantifiable metric detected — placeholder added")
        delta += 12
    else:
        changes.append("Metric already present — formatting preserved")

    # 3. Trim passive "the" at start
    if improved.lower().startswith("the "):
        improved = improved[4:]
        changes.append("Removed unnecessary article at start")
        delta += 3

    # 4. Ensure capital first letter
    if improved and improved[0].islower():
        improved = improved[0].upper() + improved[1:]

    # 5. Remove trailing whitespace artifacts
    improved = improved.strip()

    if not changes:
        changes.append("Bullet is already well-formed")

    return BulletImprovement(
        original=original,
        improved=improved,
        changes=changes,
        impact_delta=min(delta, 25),
    )


def _api_improve_batch(bullets: List[str]) -> List[BulletImprovement]:
    """Call Anthropic API to rewrite multiple bullets at once."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return [_heuristic_improve(b) for b in bullets]

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        bullets_json = json.dumps([{"id": i, "text": b} for i, b in enumerate(bullets)], indent=2)

        prompt = f"""You are a professional resume coach. Rewrite these resume bullet points to be stronger.

Rules:
- Start each bullet with a strong action verb (Led, Built, Designed, Reduced, Increased, etc.)
- Add or strengthen quantifiable metrics where possible (%, numbers, scale, time)
- Remove passive language ("helped", "assisted", "worked on")
- Keep bullets under 20 words
- If no metric is present, add a realistic placeholder like "[+X%]" or "[N users]"

BULLETS TO IMPROVE:
{bullets_json}

Return ONLY a JSON array with this exact structure:
[
  {{
    "id": 0,
    "improved": "rewritten bullet text",
    "changes": ["change 1", "change 2"],
    "impact_delta": 15
  }}
]

impact_delta = estimated score improvement from 0-25. No markdown, no explanation.
"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Strip markdown fences
        raw = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
        parsed = json.loads(raw)

        results = []
        by_id = {item["id"]: item for item in parsed}
        for i, original in enumerate(bullets):
            if i in by_id:
                d = by_id[i]
                results.append(BulletImprovement(
                    original=original,
                    improved=d.get("improved", original),
                    changes=d.get("changes", []),
                    impact_delta=min(int(d.get("impact_delta", 10)), 25),
                ))
            else:
                results.append(_heuristic_improve(original))
        return results

    except Exception as e:
        # Graceful fallback
        return [_heuristic_improve(b) for b in bullets]


def improve_bullets(bullets: List[str], use_ai: bool = True) -> List[BulletImprovement]:
    """
    Main entry point. Improve a list of resume bullet points.

    Args:
        bullets:  List of raw bullet text strings.
        use_ai:   If True, use Anthropic API (falls back to heuristics if no key).

    Returns:
        List of BulletImprovement objects.
    """
    if not bullets:
        return []

    # Deduplicate and clean
    cleaned = [b.strip() for b in bullets if b.strip()]
    if not cleaned:
        return []

    if use_ai and os.environ.get("ANTHROPIC_API_KEY"):
        # Process in batches of 6 to keep prompts focused
        results = []
        for i in range(0, len(cleaned), 6):
            batch = cleaned[i:i+6]
            results.extend(_api_improve_batch(batch))
        return results
    else:
        return [_heuristic_improve(b) for b in cleaned]


def extract_bullets_from_result(result: dict) -> List[str]:
    """Extract raw bullet excerpts from agent analysis result."""
    bullets = []
    exp = result.get("experience", {})
    for b in exp.get("bullet_quality", []):
        excerpt = b.get("bullet_excerpt", "")
        if excerpt and len(excerpt) > 10:
            bullets.append(excerpt)
    return bullets
