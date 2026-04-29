import os
import requests

API_KEY = "F8GstZbcQIB090NSZ38eEEmsNvaMZtJXuMSXALIX"  # set this in your shell
CONGRESS = 117  # change this to any Congress number you want
CHAMBER = "house"  # "senate" or "house"


def chamber_api_value(chamber):
    """Map user CHAMBER to Congress.gov term chamber string (lowercased for compare)."""
    key = (chamber or "").strip().lower()
    if key == "senate":
        return "senate"
    if key == "house":
        return "house of representatives"
    raise ValueError('CHAMBER must be "senate" or "house"')


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def served_in_chamber(member, congress, chamber_want_lower):
    """
    Return True if this member has a term in the specified Congress in the wanted chamber.
    chamber_want_lower: e.g. "senate" or "house of representatives" (from chamber_api_value).
    Handles different JSON shapes defensively.
    """
    want = chamber_want_lower
    terms = member.get("terms", {})
    items = terms.get("item", [])
    for term in as_list(items):
        chamber = (term.get("chamber") or "").lower()
        term_congress = term.get("congress")

        # On /member/congress/{congress}, list items are already scoped to the
        # requested congress and often omit term["congress"] at this level.
        # So chamber match alone is sufficient when congress is missing.
        if chamber != want:
            continue

        if term_congress is None or str(term_congress) == str(congress):
            return True
    return False


def fetch_all_members(congress):
    if not API_KEY:
        raise RuntimeError("Set CONGRESS_API_KEY environment variable first.")

    members = []
    base_url = f"https://api.congress.gov/v3/member/congress/{congress}"
    params = {
        "api_key": API_KEY,
        "format": "json",
        "limit": 250,   # max page size is typically 250
        "offset": 0,
    }

    url = base_url
    while url:
        request_params = params if url == base_url else {"api_key": API_KEY}
        resp = requests.get(url, params=request_params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        members.extend(data.get("members", []))

        # After first request, follow server-provided next URL directly
        url = data.get("pagination", {}).get("next")
        params = None

    return members


def main():
    want_chamber = chamber_api_value(CHAMBER)
    all_members = fetch_all_members(CONGRESS)

    # Keep only members of CHAMBER in the specified Congress
    in_chamber = [m for m in all_members if served_in_chamber(m, CONGRESS, want_chamber)]

    # Deduplicate by bioguide ID in case API returns repeated entries
    dedup = {}
    for m in in_chamber:
        bioguide = m.get("bioguideId")
        if bioguide:
            dedup[bioguide] = m

    # Sort by state, then name
    sorted_members = sorted(
        dedup.values(),
        key=lambda m: (m.get("state", ""), m.get("name", ""))
    )

    for m in sorted_members:
        bioguide = m.get("bioguideId", "Unknown")
        name = m.get("name", "Unknown")
        state = m.get("state", "Unknown")
        party = m.get("partyName", m.get("party", "Unknown"))
        print(f"{bioguide} | {name} | {state} | {party}")


if __name__ == "__main__":
    main()