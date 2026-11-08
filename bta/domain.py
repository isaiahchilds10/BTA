"""Canonical BTA domain objects and market semantics (not claims of book availability)."""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
import math

SPORTS = ("NBA", "NFL", "CFB")
LABELS = ("BETTER", "SAME", "MIXED", "WORSE", "NOT_ASSESSED")
SPORT_MARKETS = {
    "NBA": ["points", "rebounds", "assists", "three_pointers_made", "steals", "blocks", "points_rebounds_assists", "points_rebounds", "points_assists", "rebounds_assists", "steals_blocks", "moneyline", "spread", "total"],
    "NFL": ["passing_yards", "passing_touchdowns", "passing_attempts", "completions", "rushing_yards", "rushing_attempts", "receiving_yards", "receptions", "rushing_receiving_yards", "anytime_td", "quarter_rushing_yards", "moneyline", "spread", "total"],
    "CFB": ["moneyline", "spread", "total", "passing_yards", "rushing_yards", "receiving_yards"],
}
CFB_SCRIPTS = (
    "Expected performance", "Underdog leads 10–0 / 14–0", "Favorite loses turnover margin by two",
    "Favorite primary strength neutralized", "One-score fourth quarter",
)
NFL_SCRIPTS = (
    "Favorite blowout", "Underdog blowout / upset", "Close competitive game",
    "Low-scoring defensive game", "High-scoring shootout",
)
NBA_SCRIPTS = (
    "Player's team dominates", "Player's team trails substantially", "Close full-minute game",
    "Low-pace / defensive game", "High-pace / high-usage game",
)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def implied_probability(american: int | None) -> float | None:
    if american is None or american == 0:
        return None
    if abs(american) < 100:
        raise ValueError("American odds must be at least +100 or at most -100")
    return 100 / (american + 100) if american > 0 else -american / (-american + 100)


def selection_hit(value: float, threshold: float, direction: str, inclusive: bool = False) -> str:
    """Evaluate numeric-only outcome; does NOT handle injury, void, corrections, or special rules."""
    if direction in {"YES", "OVER"}:
        if value > threshold or (inclusive and value == threshold):
            return "HIT"
        return "PUSH" if direction == "OVER" and not inclusive and value == threshold else "MISS"
    if direction in {"NO", "UNDER"}:
        if value < threshold or (value == threshold and ((direction == "NO" and not inclusive) or (direction == "UNDER" and inclusive))):
            return "HIT"
        return "PUSH" if direction == "UNDER" and not inclusive and value == threshold else "MISS"
    raise ValueError("Unsupported direction")


@dataclass
class Game:
    id: str
    sport: str
    start_time: str
    away: str
    home: str
    state: str
    away_id: str = ""
    home_id: str = ""
    score: str = ""
    detail: str = ""
    source_url: str = ""
    checked_at: str = ""
    source_status: str = "UNAVAILABLE"
    league: str = ""


@dataclass
class Selection:
    id: str
    sport: str
    game_id: str
    game_label: str
    game_start: str
    subject: str
    market: str
    direction: str
    threshold: float | None
    inclusive: bool = False
    platform: str = "User-entered"
    american_odds: int | None = None
    athlete_id: str = ""
    team_id: str = ""
    team_role: str = ""
    market_verified: bool = False
    market_source_url: str = ""
    market_observed_at: str = ""
    quote_source_name: str = ""
    provider_market_id: str = ""
    settlement_verified: bool = False
    created_at: str = field(default_factory=utcnow)
    notes: str = ""
    game_status: str = ""
    jurisdiction: str = ""  # Bookmaker rules territory selected by user; not geolocation evidence.

    @classmethod
    def new(cls, **kwargs: Any) -> "Selection":
        return cls(id=str(uuid4()), **kwargs)

    def validate(self) -> None:
        if self.sport not in SPORTS or self.market not in SPORT_MARKETS[self.sport]:
            raise ValueError("Sport/market combination is unsupported")
        if self.direction not in {"OVER", "UNDER", "YES", "NO"}:
            raise ValueError("Direction must be OVER, UNDER, YES or NO")
        if not self.subject.strip() or len(self.subject) > 100:
            raise ValueError("Supply a player or team name under 100 characters")
        if self.market == "moneyline" and self.direction not in {"YES", "NO"}:
            raise ValueError("Moneyline requires YES or NO selection")
        if self.market != "moneyline":
            if self.threshold is None or not math.isfinite(float(self.threshold)):
                raise ValueError("A finite numeric threshold is required")
        if self.american_odds is not None:
            implied_probability(self.american_odds)
        if self.jurisdiction and (len(self.jurisdiction)!=2 or not self.jurisdiction.isalpha()):
            raise ValueError("Jurisdiction must be a two-letter state abbreviation")
        if len(self.notes) > 1000:
            raise ValueError("Notes too long")

    def asdict(self) -> dict:
        return asdict(self)


def scripts_for(selection: Selection) -> tuple[str, ...]:
    if selection.sport == "CFB" and selection.market == "moneyline":
        return CFB_SCRIPTS
    if selection.sport == "NBA":
        return NBA_SCRIPTS
    return NFL_SCRIPTS


def overlaps(a: Selection, b: Selection) -> list[str]:
    reasons = []
    if a.game_id and a.game_id == b.game_id and a.sport == b.sport:
        reasons.append("Same game: pace, injuries and game script may affect both legs")
    if a.subject.casefold().strip() == b.subject.casefold().strip() and a.sport == b.sport:
        reasons.append("Same player/team: shared availability or performance exposure")
        if a.market == b.market:
            reasons.append("Same market: potentially nested or overlapping thresholds")
            if a.direction == b.direction and a.threshold is not None and b.threshold is not None:
                if a.threshold != b.threshold:
                    reasons.append("Nested alternate thresholds: one outcome can imply the other")
    return reasons
