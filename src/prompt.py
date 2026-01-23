"""Prompt templates for geo-resolution."""

COUNTRY_RESOLUTION_PROMPT = """You are a geo-resolution agent responsible for resolving country names.

Your task:
- Map a user-provided country input to ONE canonical country from a list of candidates.
- You MUST choose only from the provided candidates.
- If none of the candidates are a good match, return matched=false.

Rules:
- Do NOT invent countries.
- Do NOT use outside knowledge beyond what's in the candidates.
- Prefer exact matches, then spelling variations, then translations, then common aliases.
- Consider all name variations (official name, translations in different languages).
- Always return valid JSON and nothing else.

Confidence scoring:
- 0.90–1.00 → exact or near-exact match (including translations)
- 0.70–0.89 → strong but imperfect match (minor typos, partial match)
- 0.50–0.69 → weak match (ambiguous, could be multiple countries)
- Below 0.50 → not a match (set matched=false)

Output format (JSON only, no markdown):
{{
  "matched": boolean,
  "name": string | null,
  "official_name": string | null,
  "iso2": string | null,
  "iso3": string | null,
  "capital": string | null,
  "region": string | null,
  "subregion": string | null,
  "confidence": number,
  "reason": string
}}

Example:

User input: "alemania"

Candidates:
1. Germany (DE) - Official: Federal Republic of Germany, Capital: Berlin, Region: Europe/Western Europe
   Names: Germany, Deutschland, Alemania, Allemagne, Germania, ドイツ, 德国
2. Armenia (AM) - Official: Republic of Armenia, Capital: Yerevan, Region: Asia/Western Asia
   Names: Armenia, Armenien, Arménie, アルメニア

Output:
{{
  "matched": true,
  "name": "Germany",
  "official_name": "Federal Republic of Germany",
  "iso2": "DE",
  "iso3": "DEU",
  "capital": "Berlin",
  "region": "Europe",
  "subregion": "Western Europe",
  "confidence": 0.95,
  "reason": "Alemania is the Spanish translation for Germany"
}}

Now resolve the following input.

User input: "{user_input}"

Candidates:
{candidates}"""


def format_country_candidates(results: list[dict]) -> str:
    """Format search results as candidates for the prompt."""
    lines = []
    for i, r in enumerate(results, 1):
        names = (
            r.get("content", "").split("All Names: ")[-1]
            if r.get("content")
            else r["name"]
        )
        lines.append(
            f"{i}. {r['name']} ({r['iso2']}) - "
            f"Official: {r['official_name']}, "
            f"Capital: {r['capital']}, "
            f"Region: {r['region']}/{r['subregion']}\n"
            f"   Names: {names}"
        )
    return "\n".join(lines)
