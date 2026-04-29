import os
import requests

API_KEY = "F8GstZbcQIB090NSZ38eEEmsNvaMZtJXuMSXALIX"  # set this in your shell
CONGRESS = 118  # change this to any Congress number you want


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def served_in_senate(member, congress):
    """
    Return True if this member has a term in the specified Congress in the Senate.
    Handles different JSON shapes defensively.
    """
    terms = member.get("terms", {})
    items = terms.get("item", [])
    for term in as_list(items):
        term_congress = str(term.get("congress", ""))
        chamber = (term.get("chamber") or "").lower()
        if term_congress == str(congress) and chamber == "senate":
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
    all_members = fetch_all_members(CONGRESS)

    # Keep only Senate members in the specified Congress
    senators = [m for m in all_members if served_in_senate(m, CONGRESS)]

    # Deduplicate by bioguide ID in case API returns repeated entries
    dedup = {}
    for m in senators:
        bioguide = m.get("bioguideId")
        if bioguide:
            dedup[bioguide] = m

    # Sort by state, then name
    sorted_senators = sorted(
        dedup.values(),
        key=lambda m: (m.get("state", ""), m.get("name", ""))
    )

    for m in sorted_senators:
        name = m.get("name", "Unknown")
        state = m.get("state", "Unknown")
        party = m.get("partyName", m.get("party", "Unknown"))
        print(f"{name} | {state} | {party}")


if __name__ == "__main__":
    main()