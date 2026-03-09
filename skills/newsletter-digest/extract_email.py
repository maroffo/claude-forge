# ABOUTME: Extract text content from gog gmail thread JSON output
# ABOUTME: Handles multipart/alternative, nested parts, base64 decoding

"""
Usage:
    gog gmail thread get <threadId> --account=maroffo@gmail.com --json | python3 extract_email.py
    gog gmail thread get <threadId> --account=maroffo@gmail.com --json | python3 extract_email.py --meta
    gog gmail thread get <threadId> --account=maroffo@gmail.com --json | python3 extract_email.py --max-chars 5000

Outputs plain text body of the first message in the thread.
With --meta, also prints From, Subject, Date as header lines.
"""

import sys
import json
import base64
import argparse
import email.utils
from datetime import datetime


def decode_body(data: str) -> str:
    """Decode base64url-encoded email body."""
    if not data:
        return ""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")


def extract_text_from_payload(payload: dict) -> str:
    """Recursively extract text/plain from a MIME payload."""
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return decode_body(data)

    parts = payload.get("parts", [])
    for part in parts:
        text = extract_text_from_payload(part)
        if text:
            return text

    # Fallback: if no text/plain found, try text/html and strip tags
    if mime_type == "text/html":
        data = payload.get("body", {}).get("data", "")
        html = decode_body(data)
        return strip_html(html)

    for part in parts:
        if part.get("mimeType") == "text/html":
            data = part.get("body", {}).get("data", "")
            html = decode_body(data)
            return strip_html(html)

    return ""


def strip_html(html: str) -> str:
    """Minimal HTML tag stripping (no dependencies)."""
    import re
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_header(message: dict, name: str) -> str:
    """Extract a header value from a Gmail message."""
    headers = message.get("payload", {}).get("headers", [])
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def format_date(date_str: str) -> str:
    """Parse email date header into YYYY-MM-DD."""
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return date_str


def main():
    parser = argparse.ArgumentParser(description="Extract email text from gog JSON")
    parser.add_argument("--meta", action="store_true", help="Include From/Subject/Date header")
    parser.add_argument("--max-chars", type=int, default=0, help="Truncate output to N chars (0=unlimited)")
    parser.add_argument("--message-index", type=int, default=0, help="Which message in thread (default: first)")
    args = parser.parse_args()

    data = json.load(sys.stdin)

    thread = data.get("thread", data)
    messages = thread.get("messages", [])

    if not messages:
        print("Error: no messages in thread", file=sys.stderr)
        sys.exit(1)

    idx = min(args.message_index, len(messages) - 1)
    message = messages[idx]

    if args.meta:
        from_addr = extract_header(message, "From")
        subject = extract_header(message, "Subject")
        date = format_date(extract_header(message, "Date"))
        print(f"From: {from_addr}")
        print(f"Subject: {subject}")
        print(f"Date: {date}")
        print("---")

    payload = message.get("payload", {})
    text = extract_text_from_payload(payload)

    if not text:
        snippet = message.get("snippet", "")
        if snippet:
            text = snippet
        else:
            print("Error: no text content found", file=sys.stderr)
            sys.exit(1)

    if args.max_chars > 0:
        text = text[:args.max_chars]

    print(text)


if __name__ == "__main__":
    main()
