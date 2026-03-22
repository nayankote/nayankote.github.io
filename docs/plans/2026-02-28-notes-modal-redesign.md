# Notes Modal Redesign + Full-Text Resync

Date: 2026-02-28

## Problem

1. The notes modal displays `note.text` (body content) as a large bold title, and `note.subject` (email subject) as small italic text at the bottom — the wrong way around.
2. Notes are truncated to 200 chars at ingestion time in the Gmail script, losing content permanently.
3. Historical notes in `notes_raw.json` already have truncated text.

## Design

### 1. Remove truncation from Gmail ingestion (`notes_gmail_to_github.gs`)
- Delete the 200-char truncation block (`substring(0, 197) + '...'`).
- Future notes will store full body text.

### 2. Add `reprocessAllEmails()` to Gmail script
- Searches Gmail for ALL emails matching the note pattern, including those already labeled "Processed".
- Rebuilds `notes_raw.json` from scratch with full text (no truncation).
- Commits to GitHub. Run once manually from script.google.com to recover historical notes.

### 3. Restructure notes modal (`notes/index.html`)
New order:
- **Subject** (`note.subject`) — body font size (1em), bold
- **Note body** (`note.text`) — full text, not truncated, normal weight, scrollable
- **Date** — small, muted (keep as-is)
- **Category** (`cluster label`) — small italic, accent color (keep as-is)

### Data note
Existing notes in `notes_raw.json` are already truncated. Running `reprocessAllEmails()` once will overwrite the file with full text from Gmail, after which the GitHub Action will re-run `process_notes.py` to regenerate `notes_processed.json`.
