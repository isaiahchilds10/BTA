"""Conservative quick-add parser. No guess is converted into a verified market."""
from __future__ import annotations
import re
from bta.domain import SPORT_MARKETS

ALIASES = {
    "receiving yards":"receiving_yards", "receiving yard":"receiving_yards",
    "rushing yards":"rushing_yards", "rush yards":"rushing_yards",
    "passing yards":"passing_yards", "pass yards":"passing_yards",
    "points":"points", "rebounds":"rebounds", "assists":"assists",
    "receptions":"receptions", "catches":"receptions",
    "three pointers made":"three_pointers_made", "3 pointers made":"three_pointers_made",
    "3pm":"three_pointers_made", "threes":"three_pointers_made",
    "rushing attempts":"rushing_attempts", "carries":"rushing_attempts",
    "passing attempts":"passing_attempts", "pass attempts":"passing_attempts",
    "completions":"completions", "passing touchdowns":"passing_touchdowns",
    "rushing receiving yards":"rushing_receiving_yards",
    "points rebounds assists":"points_rebounds_assists", "pra":"points_rebounds_assists",
    "anytime touchdown":"anytime_td", "anytime td":"anytime_td",
}


def parse_one(text: str, sport: str) -> dict:
    """Understands `Player 20+ receiving yards`, `Player over 20.5 points`, `NO Player 100+ rushing yards`.
    Ambiguous inputs return an explicit blocker instead of silent corrections.
    """
    text = text.strip()
    if not text or len(text) > 240:
        raise ValueError("Use a selection under 240 characters")
    normalized = re.sub(r"\s+", " ", text.replace("—", " ").replace("–", " ")).strip()
    match = re.search(r"\b(OVER|UNDER|YES|NO)\s+(\d+(?:\.\d+)?)\b", normalized, re.I)
    prefix_no = re.match(r"^NO\s+", normalized, re.I)
    inclusive = False
    if match:
        direction = match.group(1).upper()
        threshold = float(match.group(2))
        subject = normalized[:match.start()].strip()
        trailing = normalized[match.end():].strip()
    else:
        match = re.search(r"(?<!\d)(\d+(?:\.\d+)?)\s*\+", normalized)
        if not match:
            raise ValueError("Cannot safely identify exact direction and threshold")
        direction = "NO" if prefix_no else "YES"
        inclusive = True
        threshold = float(match.group(1))
        subject = normalized[:match.start()].strip()
        trailing = normalized[match.end():].strip()
        if prefix_no:
            subject = re.sub(r"^NO\s+", "",subject,flags=re.I)
    market_label = re.sub(r"[^a-zA-Z0-9 ]", " ", trailing).lower().strip()
    market = ALIASES.get(market_label)
    if not market or market not in SPORT_MARKETS[sport]:
        raise ValueError(f"Market '{trailing}' not recognized for {sport}; enter manually")
    if not subject:
        raise ValueError("Player or team name was not identified")
    return {"subject":subject,"market":market,"direction":direction,"threshold":threshold,"inclusive":inclusive,"notes":f"Parsed from: {text}"}


def parse_bulk(text: str, sport: str) -> tuple[list[dict], list[str]]:
    ready, errors = [], []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            ready.append(parse_one(line,sport))
        except ValueError as exc:
            errors.append(f"Line {number}: {exc}")
    return ready, errors
