"""Geo-resolution CLI."""

import sys
import time

from src.config import validate_config
from src.resolver import resolve_country


def main():
    """Entry point."""
    validate_config()

    if len(sys.argv) < 2:
        print("Usage: python -m src.main <country_query>")
        print()
        print("Examples:")
        print("  python -m src.main 'alemania'")
        print("  python -m src.main 'united states'")
        print("  python -m src.main 'brasil'")
        print("  python -m src.main 'japon'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Resolving: '{query}'")
    print("-" * 50)

    start_time = time.time()
    result = resolve_country(query)
    elapsed_time = time.time() - start_time

    print(f"Time: {elapsed_time:.2f}s")
    print("-" * 50)

    if result.matched:
        print(f"Match: {result.name} ({result.iso2})")
        print(f"Official: {result.official_name}")
        print(f"Capital: {result.capital}")
        print(f"Region: {result.region}, {result.subregion}")
        print(f"Confidence: {result.confidence:.0%}")
        print(f"Reason: {result.reason}")
    else:
        print("No match found")
        print(f"Reason: {result.reason}")


if __name__ == "__main__":
    main()
