"""Data models for geo-resolution results."""

from dataclasses import dataclass


@dataclass
class CountryResult:
    """Result of country resolution."""

    matched: bool
    name: str | None = None
    official_name: str | None = None
    iso2: str | None = None
    iso3: str | None = None
    capital: str | None = None
    region: str | None = None
    subregion: str | None = None
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
