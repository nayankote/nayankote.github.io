# Notes Modal Redesign + Full-Text Resync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure the notes modal to show subject as bold header, full note body text, and small italic category — and remove the Gmail ingestion truncation that was silently cutting notes to 200 chars.

**Architecture:** Two independent changes: (1) fix the Google Apps Script (`notes_gmail_to_github.gs`) to remove truncation and add a full resync function, (2) update `notes/index.html` modal HTML/CSS/JS to display fields in the correct order with correct styling.

**Tech Stack:** Vanilla HTML/CSS/JS (modal), Google Apps Script (Gmail ingestion), Python (note processing pipeline already exists and doesn't need changes).

---

### Task 1: Remove 200-char truncation from Gmail ingestion script

**Files:**
- Modify: `scripts/notes_gmail_to_github.gs:108-111`

**Step 1: Open the file and locate the truncation block**

Read `scripts/notes_gmail_to_github.gs`. Find lines 108-111:
```javascript
// Truncate to 200 chars
if (noteText && noteText.length > 200) {
  noteText = noteText.substring(0, 197) + '...';
}
```

**Step 2: Delete the truncation block**

Remove those 4 lines entirely. The code around it should flow from the line-break normalization directly into the `if (noteText)` check:

```javascript
// Normalize line breaks: replace \r\n and \r with single space, collapse multiple spaces
if (noteText) {
  noteText = noteText.replace(/\r\n/g, ' ').replace(/\r/g, ' ').replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
}

if (noteText) {
  newNotes.push({
```

**Step 3: Commit**

```bash
git add scripts/notes_gmail_to_github.gs
git commit -m "fix: remove 200-char truncation from Gmail note ingestion"
```

---

### Task 2: Add `reprocessAllEmails()` resync function to Gmail script

**Files:**
- Modify: `scripts/notes_gmail_to_github.gs` (append new function after `testProcessEmails()`)

**Step 1: Add the reprocessAllEmails function**

Append the following function to the end of `scripts/notes_gmail_to_github.gs`, after `testProcessEmails()`:

```javascript
/**
 * Full resync: re-reads ALL note emails (including already-processed ones)
 * and rebuilds notes_raw.json from scratch with full text.
 * Run once manually from script.google.com after removing the truncation limit.
 */
function reprocessAllEmails() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  const owner = props.getProperty('GITHUB_OWNER');
  const repo = props.getProperty('GITHUB_REPO');

  if (!token || !owner || !repo) {
    Logger.log('Missing configuration. Set GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO in script properties.');
    return;
  }

  // Search ALL note emails, including already-processed ones (no -label filter)
  const threads = GmailApp.search('subject:(note: OR n:)', 0, 500);

  if (threads.length === 0) {
    Logger.log('No note emails found.');
    return;
  }

  Logger.log(`Found ${threads.length} note email threads. Rebuilding from scratch...`);

  const allNotes = [];

  for (const thread of threads) {
    const message = thread.getMessages()[0];
    let subject = message.getSubject();

    if (!/^(note:|n:)/i.test(subject)) {
      continue;
    }

    const body = message.getPlainBody().trim();
    const title = subject.replace(/^(note:|n:)\s*/i, '').trim();

    let noteText = body || title;

    // Normalize line breaks (same as processNewEmails, but NO truncation)
    if (noteText) {
      noteText = noteText.replace(/\r\n/g, ' ').replace(/\r/g, ' ').replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
    }

    if (noteText) {
      allNotes.push({
        id: Utilities.getUuid(),
        text: noteText,
        subject: title || null,
        timestamp: message.getDate().toISOString(),
        source: 'email'
      });
    }
  }

  Logger.log(`Collected ${allNotes.length} notes. Committing to GitHub...`);

  // Get current file SHA (needed for update, even though we're overwriting content)
  const currentFile = getGitHubFile(token, owner, repo, CONFIG.FILE_PATH);
  const newData = { notes: allNotes };

  const success = updateGitHubFile(
    token, owner, repo, CONFIG.FILE_PATH,
    JSON.stringify(newData, null, 2),
    `Resync: rebuild ${allNotes.length} notes from Gmail with full text`,
    currentFile ? currentFile.sha : null
  );

  if (success) {
    Logger.log(`Done! Rebuilt notes_raw.json with ${allNotes.length} notes (full text, no truncation).`);
    Logger.log('GitHub Actions will now re-run process_notes.py to regenerate notes_processed.json.');
  } else {
    Logger.log('Failed to update GitHub file.');
  }
}
```

**Step 2: Verify the function reuses `getGitHubFile` and `updateGitHubFile`**

Confirm that both helper functions are already defined in the file (they are, at lines ~193 and ~217). No new helpers needed.

**Step 3: Commit**

```bash
git add scripts/notes_gmail_to_github.gs
git commit -m "feat: add reprocessAllEmails() to rebuild notes_raw.json from Gmail with full text"
```

---

### Task 3: Restructure the notes modal in index.html

**Files:**
- Modify: `notes/index.html`

The modal currently has this structure:
```html
<div class="modal-header">
    <div class="modal-title" id="modalTitle"></div>  <!-- currently shows note.text -->
    <span class="close">...</span>
</div>
<div class="modal-metadata">
    <div class="modal-date" id="modalDate"></div>
    <div class="modal-cluster" id="modalCluster"></div>
</div>
<div class="modal-subject" id="modalSubject"></div>  <!-- currently shows note.subject -->
```

Target structure:
```
[subject - bold, body font size]   [×]
[date]  [category tag]
[full note body text]
```

**Step 1: Update the CSS**

Find the `.modal-title` CSS block (around line 111) and change `font-size` to `1em`:

Old:
```css
.modal-title {
    font-size: 1.1em;
    font-weight: 600;
    ...
}
```

New:
```css
.modal-title {
    font-size: 1em;
    font-weight: 600;
    color: var(--color-text, #333);
    font-family: 'Libre Baskerville', serif;
    line-height: 1.6;
    flex: 1;
    padding-right: 16px;
    white-space: pre-wrap;
    word-wrap: break-word;
}
```

Then add a new CSS class for the note body text after `.modal-subject`:

```css
.modal-body {
    font-size: 1em;
    color: var(--color-text, #333);
    font-family: 'Libre Baskerville', serif;
    line-height: 1.7;
    margin-top: 16px;
    white-space: pre-wrap;
    word-wrap: break-word;
}
```

And update `.modal-subject` to be the cluster/category style (it currently shows subject but will now show category in italic):
```css
.modal-subject {
    font-size: 0.85em;
    color: #64748b;
    font-style: italic;
    margin-top: 12px;
}
```
(This is already correct — no change needed to this rule.)

**Step 2: Update the modal HTML**

Find the modal HTML block (around line 295) and add a `modal-body` div:

Old:
```html
<div id="noteModal" class="modal" onclick="if(event.target===this) closeModal()">
    <div class="modal-content">
        <div class="modal-header">
            <div class="modal-title" id="modalTitle"></div>
            <span class="close" onclick="closeModal()">&times;</span>
        </div>
        <div class="modal-metadata">
            <div class="modal-date" id="modalDate"></div>
            <div class="modal-cluster" id="modalCluster"></div>
        </div>
        <div class="modal-subject" id="modalSubject"></div>
    </div>
</div>
```

New:
```html
<div id="noteModal" class="modal" onclick="if(event.target===this) closeModal()">
    <div class="modal-content">
        <div class="modal-header">
            <div class="modal-title" id="modalTitle"></div>
            <span class="close" onclick="closeModal()">&times;</span>
        </div>
        <div class="modal-metadata">
            <div class="modal-date" id="modalDate"></div>
            <div class="modal-cluster" id="modalCluster"></div>
        </div>
        <div class="modal-body" id="modalBody"></div>
        <div class="modal-subject" id="modalSubject"></div>
    </div>
</div>
```

**Step 3: Update the `openModal()` JavaScript function**

Find the `openModal` function (around line 482):

Old:
```javascript
function openModal(note) {
    document.getElementById('modalTitle').textContent = note.text;
    document.getElementById('modalDate').textContent = formatDate(note.timestamp);
    document.getElementById('modalCluster').textContent = getClusterLabel(note.cluster_id);

    const subjectEl = document.getElementById('modalSubject');
    if (note.subject) {
        subjectEl.textContent = `subject: "${note.subject}"`;
        subjectEl.style.display = 'block';
    } else {
        subjectEl.style.display = 'none';
    }

    document.getElementById('noteModal').style.display = 'block';
}
```

New:
```javascript
function openModal(note) {
    // Header: subject (bold, body font size)
    const titleEl = document.getElementById('modalTitle');
    if (note.subject) {
        titleEl.textContent = note.subject;
        titleEl.style.display = 'block';
    } else {
        titleEl.style.display = 'none';
    }

    document.getElementById('modalDate').textContent = formatDate(note.timestamp);
    document.getElementById('modalCluster').textContent = getClusterLabel(note.cluster_id);

    // Body: full note text
    document.getElementById('modalBody').textContent = note.text;

    // Category: small italic (cluster label already shown above, hide old subject field)
    document.getElementById('modalSubject').style.display = 'none';

    document.getElementById('noteModal').style.display = 'block';
}
```

**Step 4: Commit**

```bash
git add notes/index.html
git commit -m "feat: restructure notes modal - subject as header, full body text, remove subject field"
```

---

### Task 4: Push and verify

**Step 1: Pull latest to avoid conflicts**

```bash
git pull --rebase
```

**Step 2: Push**

```bash
git push
```

**Step 3: Verify in browser**

Open `https://nayankote.com/notes/`, click a note node, and confirm:
- Subject appears at top, bold, same size as body text
- Full note body text appears below (not truncated)
- Category tag and date still show correctly

**Step 4: Run reprocessAllEmails() in Google Apps Script**

Go to script.google.com, open the notes project, and run `reprocessAllEmails()` once. Check the logs to confirm it rebuilt `notes_raw.json`. GitHub Actions will then re-run `process_notes.py` automatically.
