#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CfP Page Fetcher

Fetches and extracts Call for Papers details from a conference URL.
Returns structured JSON that can be used by the cfp-helper skill.

Usage:
    python fetch_cfp.py <url>
    python fetch_cfp.py https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/program/cfp/

Output:
    JSON with extracted CfP details
"""

import sys
import json
import re
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional
import argparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print(json.dumps({
        "error": "Missing dependencies. Install with: pip install requests beautifulsoup4",
        "install_command": "pip install requests beautifulsoup4"
    }))
    sys.exit(1)


def fetch_page(url: str) -> Optional[str]:
    """Fetch the HTML content of a URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return None


def extract_dates(text: str) -> list[str]:
    """Extract date patterns from text."""
    patterns = [
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:-\d{1,2})?,?\s*\d{4}\b',
        r'\b\d{1,2}(?:-\d{1,2})?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s*\d{4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b',
    ]
    dates = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)
    return list(set(dates))


def extract_durations(text: str) -> list[dict]:
    """Extract session duration patterns."""
    patterns = [
        r'(\d+)\s*(?:min(?:ute)?s?|mins?)\b',
        r'(\d+(?:\.\d+)?)\s*(?:hour|hr)s?\b',
    ]
    durations = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if 'hour' in pattern.lower() or 'hr' in pattern.lower():
                durations.append({"value": int(float(match) * 60), "unit": "minutes"})
            else:
                durations.append({"value": int(match), "unit": "minutes"})
    return durations


def extract_character_limits(text: str) -> dict:
    """Extract character/word limits."""
    limits = {}

    # Character limits
    char_patterns = [
        r'(?:max(?:imum)?|limit|up to)\s*[:\s]*(\d+)\s*character',
        r'(\d+)\s*character\s*(?:max(?:imum)?|limit)',
    ]
    for pattern in char_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            limits['characters'] = int(matches[0])
            break

    # Word limits
    word_patterns = [
        r'(?:max(?:imum)?|limit|up to)\s*[:\s]*(\d+)\s*word',
        r'(\d+)\s*word\s*(?:max(?:imum)?|limit)',
    ]
    for pattern in word_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            limits['words'] = int(matches[0])
            break

    return limits


def extract_session_types(soup: BeautifulSoup, text: str) -> list[dict]:
    """Extract session types and their details."""
    session_types = []

    # Common session type keywords
    type_keywords = [
        'presentation', 'talk', 'session', 'lightning', 'tutorial',
        'workshop', 'panel', 'keynote', 'poster', 'bof', 'birds of a feather',
        'meetup', 'activity', 'booth', 'demo'
    ]

    # Look for tables with session info
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_text = ' '.join(cell.get_text().strip() for cell in cells).lower()
            for keyword in type_keywords:
                if keyword in row_text:
                    # Try to extract duration
                    duration_match = re.search(r'(\d+)\s*(?:min|hour|hr)', row_text)
                    session_types.append({
                        "type": keyword.title(),
                        "raw_text": row_text[:200],
                        "duration": duration_match.group(0) if duration_match else None
                    })
                    break

    # Also search in lists
    lists = soup.find_all(['ul', 'ol'])
    for lst in lists:
        items = lst.find_all('li')
        for item in items:
            item_text = item.get_text().strip().lower()
            for keyword in type_keywords:
                if keyword in item_text and len(item_text) < 300:
                    duration_match = re.search(r'(\d+)\s*(?:min|hour|hr)', item_text)
                    session_types.append({
                        "type": keyword.title(),
                        "raw_text": item_text[:200],
                        "duration": duration_match.group(0) if duration_match else None
                    })
                    break

    # Deduplicate
    seen = set()
    unique_types = []
    for st in session_types:
        if st["type"] not in seen:
            seen.add(st["type"])
            unique_types.append(st)

    return unique_types


def extract_tracks(soup: BeautifulSoup, text: str) -> list[str]:
    """Extract track/topic names."""
    tracks = []

    # Look for track-related sections
    track_keywords = ['track', 'topic', 'theme', 'category', 'area']

    # Search in headers and nearby lists
    headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for header in headers:
        header_text = header.get_text().strip().lower()
        if any(kw in header_text for kw in track_keywords):
            # Look for list following this header
            next_elem = header.find_next(['ul', 'ol'])
            if next_elem:
                items = next_elem.find_all('li')
                for item in items:
                    track_name = item.get_text().strip()
                    if len(track_name) < 100:  # Reasonable track name length
                        tracks.append(track_name)

    return tracks[:20]  # Limit to 20 tracks


def extract_deadlines(soup: BeautifulSoup, text: str) -> dict:
    """Extract CfP deadlines and important dates."""
    deadlines = {}

    deadline_keywords = {
        'cfp_closes': ['cfp close', 'submission deadline', 'proposals due', 'cfp deadline', 'submit by'],
        'notification': ['notification', 'decisions', 'acceptance', 'results'],
        'event_date': ['event date', 'conference date', 'takes place'],
    }

    # Look for date patterns near keywords
    for key, keywords in deadline_keywords.items():
        for keyword in keywords:
            # Find text containing keyword
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = soup.find_all(string=pattern)
            for match in matches:
                parent = match.parent
                if parent:
                    context = parent.get_text()
                    dates = extract_dates(context)
                    if dates:
                        deadlines[key] = dates[0]
                        break
            if key in deadlines:
                break

    return deadlines


def extract_speaker_limits(text: str) -> dict:
    """Extract speaker-related limits."""
    limits = {}

    # Max proposals per person
    proposal_patterns = [
        r'(?:max(?:imum)?|up to|limit(?:ed)? to)\s*(\d+)\s*(?:proposal|submission|talk|session)s?\s*(?:per|each)\s*(?:person|individual|speaker)',
        r'(\d+)\s*(?:proposal|submission)s?\s*(?:max(?:imum)?|limit)',
    ]
    for pattern in proposal_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            limits['max_proposals_per_person'] = int(match.group(1))
            break

    # Max speakers per session
    speaker_patterns = [
        r'(?:max(?:imum)?|up to)\s*(\d+)\s*speaker',
        r'(\d+)\s*speaker\s*(?:max(?:imum)?|limit)',
    ]
    for pattern in speaker_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            limits['max_speakers_per_session'] = int(match.group(1))
            break

    return limits


def extract_review_info(text: str) -> dict:
    """Extract review process information."""
    info = {}

    # Blind review
    if re.search(r'blind\s*review', text, re.IGNORECASE):
        info['blind_review'] = True
    elif re.search(r'(?:speaker|identity)\s*(?:visible|known|revealed)', text, re.IGNORECASE):
        info['blind_review'] = False

    # Acceptance rate
    rate_match = re.search(r'(\d+)%?\s*(?:acceptance|accepted)', text, re.IGNORECASE)
    if rate_match:
        info['acceptance_rate'] = f"{rate_match.group(1)}%"

    return info


def parse_cfp_page(url: str) -> dict:
    """Main function to parse a CfP page and extract details."""

    # Determine conference name from URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('www.', '')

    html = fetch_page(url)
    if not html:
        return {
            "error": f"Failed to fetch URL: {url}",
            "url": url
        }

    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for element in soup(['script', 'style', 'nav', 'footer']):
        element.decompose()

    # Get text content
    text = soup.get_text(separator=' ', strip=True)

    # Extract page title
    title = soup.find('title')
    page_title = title.get_text().strip() if title else None

    # Try to find conference name
    h1 = soup.find('h1')
    conference_name = h1.get_text().strip() if h1 else page_title

    # Extract all information
    result = {
        "url": url,
        "domain": domain,
        "conference_name": conference_name,
        "page_title": page_title,
        "fetched_at": datetime.now().isoformat(),
        "deadlines": extract_deadlines(soup, text),
        "session_types": extract_session_types(soup, text),
        "tracks": extract_tracks(soup, text),
        "character_limits": extract_character_limits(text),
        "speaker_limits": extract_speaker_limits(text),
        "review_info": extract_review_info(text),
        "dates_found": extract_dates(text)[:10],  # First 10 dates
        "raw_text_preview": text[:2000],  # First 2000 chars for context
    }

    return result


def generate_markdown(data: dict) -> str:
    """Generate a markdown conference file from extracted data."""

    md = f"""# {data.get('conference_name', 'Conference')}

## Event Details

| Field | Value |
|-------|-------|
| **Name** | {data.get('conference_name', 'TBD')} |
| **Website** | {data.get('url', '')} |
| **Dates** | {', '.join(data.get('dates_found', [])[:3]) or 'TBD'} |

## CfP Timeline

| Milestone | Date |
|-----------|------|
| CfP Closes | {data.get('deadlines', {}).get('cfp_closes', 'TBD')} |
| Notifications | {data.get('deadlines', {}).get('notification', 'TBD')} |

## Session Types & Durations

| Type | Duration | Notes |
|------|----------|-------|
"""

    for st in data.get('session_types', []):
        md += f"| {st.get('type', '')} | {st.get('duration', 'TBD')} | |\n"

    if not data.get('session_types'):
        md += "| TBD | TBD | Check CfP page |\n"

    md += """
## Submission Constraints

### Character/Word Limits
"""

    limits = data.get('character_limits', {})
    if limits.get('characters'):
        md += f"- **Abstract:** Max {limits['characters']} characters\n"
    if limits.get('words'):
        md += f"- **Abstract:** Max {limits['words']} words\n"
    if not limits:
        md += "- Check CfP page for specific limits\n"

    speaker_limits = data.get('speaker_limits', {})
    if speaker_limits:
        md += "\n### Speaker Limits\n"
        if speaker_limits.get('max_proposals_per_person'):
            md += f"- Max {speaker_limits['max_proposals_per_person']} proposals per person\n"
        if speaker_limits.get('max_speakers_per_session'):
            md += f"- Max {speaker_limits['max_speakers_per_session']} speakers per session\n"

    review_info = data.get('review_info', {})
    if review_info:
        md += "\n### Review Process\n"
        if 'blind_review' in review_info:
            md += f"- Blind review: {'Yes' if review_info['blind_review'] else 'No'}\n"
        if review_info.get('acceptance_rate'):
            md += f"- Acceptance rate: ~{review_info['acceptance_rate']}\n"

    tracks = data.get('tracks', [])
    if tracks:
        md += "\n## Tracks / Topics\n\n"
        for i, track in enumerate(tracks, 1):
            md += f"{i}. **{track}**\n"

    md += f"""
## Raw Text Preview

<details>
<summary>First 2000 characters from CfP page (click to expand)</summary>

```
{data.get('raw_text_preview', '')[:2000]}
```

</details>

---

*Auto-generated from {data.get('url', '')} on {data.get('fetched_at', '')}*
*Review and complete missing fields manually*
"""

    return md


def main():
    parser = argparse.ArgumentParser(
        description='Fetch and extract CfP details from a conference URL'
    )
    parser.add_argument('url', help='The CfP page URL to fetch')
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'markdown', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path (optional, prints to stdout if not specified)'
    )

    args = parser.parse_args()

    # Fetch and parse
    data = parse_cfp_page(args.url)

    if 'error' in data:
        print(json.dumps(data, indent=2))
        sys.exit(1)

    # Generate output
    if args.format == 'json':
        output = json.dumps(data, indent=2)
    elif args.format == 'markdown':
        output = generate_markdown(data)
    else:  # both
        output = f"## Extracted JSON\n\n```json\n{json.dumps(data, indent=2)}\n```\n\n## Generated Markdown\n\n{generate_markdown(data)}"

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Output written to {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
