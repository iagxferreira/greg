"""Data models for geo-resolution results."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CountryResult:
    """Result of country resolution."""

    matched: bool
    name: Optional[str] = None
    official_name: Optional[str] = None
    iso2: Optional[str] = None
    iso3: Optional[str] = None
    capital: Optional[str] = None
    region: Optional[str] = None
    subregion: Optional[str] = None
    confidence: float = 0.0
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "CountryResult":
        """Create from dictionary."""
        return cls(
            matched=data.get("matched", False),
            name=data.get("name"),
            official_name=data.get("official_name"),
            iso2=data.get("iso2"),
            iso3=data.get("iso3"),
            capital=data.get("capital"),
            region=data.get("region"),
            subregion=data.get("subregion"),
            confidence=data.get("confidence", 0.0),
            reason=data.get("reason", ""),
        )

    @classmethod
    def no_match(cls, reason: str = "No matching country found") -> "CountryResult":
        """Create a no-match result."""
        return cls(matched=False, confidence=0.0, reason=reason)
