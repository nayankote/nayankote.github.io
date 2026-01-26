/**
 * Notes Email to GitHub
 *
 * SETUP INSTRUCTIONS:
 * 1. Go to script.google.com (while logged into nayankotenl@gmail.com)
 * 2. Create a new project
 * 3. Paste this entire code
 * 4. Go to Project Settings (gear icon) > Script Properties
 * 5. Add these properties:
 *    - GITHUB_TOKEN: your personal access token
 *    - GITHUB_OWNER: nayankote
 *    - GITHUB_REPO: nayankote.github.io
 * 6. Run the setup() function once (Run > Run function > setup)
 * 7. Grant permissions when prompted
 *
 * HOW TO CAPTURE NOTES:
 * - Send email to nayankotenl@gmail.com
 * - Subject: "n: optional title" or "note: optional title"
 * - Body: your actual note content
 * - Processed notes are moved to "Processed" label and marked read
 *
 * The script runs every 5 minutes automatically.
 */

const CONFIG = {
  FILE_PATH: 'notes/notes_raw.json',
  BRANCH: 'main',
  PROCESSED_LABEL: 'Processed'
};

function setup() {
  // Remove any existing triggers first
  const triggers = ScriptApp.getProjectTriggers();
  for (const trigger of triggers) {
    ScriptApp.deleteTrigger(trigger);
  }

  // Create the "Processed" label if it doesn't exist
  getOrCreateLabel(CONFIG.PROCESSED_LABEL);

  // Create time-based trigger to run every 5 minutes
  ScriptApp.newTrigger('processNewEmails')
    .timeBased()
    .everyMinutes(5)
    .create();

  Logger.log('Setup complete!');
  Logger.log('- Trigger created (runs every 5 minutes)');
  Logger.log('- "Processed" label created');
}

function getOrCreateLabel(labelName) {
  let label = GmailApp.getUserLabelByName(labelName);
  if (!label) {
    label = GmailApp.createLabel(labelName);
    Logger.log(`Created label: ${labelName}`);
  }
  return label;
}

function processNewEmails() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  const owner = props.getProperty('GITHUB_OWNER');
  const repo = props.getProperty('GITHUB_REPO');

  if (!token || !owner || !repo) {
    Logger.log('Missing configuration. Set GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO in script properties.');
    return;
  }

  // Search for emails with subject starting with "note:" or "n:"
  // Exclude already processed emails (those with the Processed label)
  const threads = GmailApp.search(`subject:(note: OR n:) -label:${CONFIG.PROCESSED_LABEL}`, 0, 20);

  if (threads.length === 0) {
    Logger.log('No new notes to process.');
    return;
  }

  const processedLabel = getOrCreateLabel(CONFIG.PROCESSED_LABEL);
  const newNotes = [];
  const threadsToLabel = [];  // Store threads to label only after successful commit
  const threadsToSkip = [];   // Threads that don't match pattern (label immediately)

  // Phase 1: Collect notes without labeling
  for (const thread of threads) {
    const message = thread.getMessages()[0];
    let subject = message.getSubject();

    // Skip if subject doesn't match our pattern - these can be labeled immediately
    if (!/^(note:|n:)/i.test(subject)) {
      threadsToSkip.push(thread);
      continue;
    }

    const body = message.getPlainBody().trim();
    const title = subject.replace(/^(note:|n:)\s*/i, '').trim();

    // Note text is the body; if no body, use the title
    let noteText = body || title;

    // Truncate to 200 chars
    if (noteText && noteText.length > 200) {
      noteText = noteText.substring(0, 197) + '...';
    }

    if (noteText) {
      newNotes.push({
        id: Utilities.getUuid(),
        text: noteText,
        subject: title || null,
        timestamp: message.getDate().toISOString(),
        source: 'email'
      });
      threadsToLabel.push(thread);
    }
  }

  // Label skipped threads immediately (non-matching subjects)
  for (const thread of threadsToSkip) {
    thread.addLabel(processedLabel);
    thread.markRead();
  }

  if (newNotes.length === 0) {
    Logger.log('No valid notes found in matched emails.');
    return;
  }

  Logger.log(`Found ${newNotes.length} new notes.`);

  // Phase 2: Get current file from GitHub
  const currentFile = getGitHubFile(token, owner, repo, CONFIG.FILE_PATH);
  let currentData = { notes: [] };

  if (currentFile && currentFile.content) {
    try {
      const decoded = Utilities.newBlob(Utilities.base64Decode(currentFile.content)).getDataAsString();
      currentData = JSON.parse(decoded);
    } catch (e) {
      Logger.log('Error parsing current file, starting fresh: ' + e);
    }
  }

  // Get existing note texts to prevent duplicates
  const existingTexts = new Set(currentData.notes.map(n => n.text));

  // Filter out any notes that already exist (by text content)
  const uniqueNewNotes = newNotes.filter(n => !existingTexts.has(n.text));

  if (uniqueNewNotes.length === 0) {
    Logger.log('All notes already exist, skipping.');
    // Label these threads since notes already exist in GitHub
    for (const thread of threadsToLabel) {
      thread.addLabel(processedLabel);
      thread.markRead();
    }
    return;
  }

  // Append only unique new notes
  currentData.notes = currentData.notes.concat(uniqueNewNotes);

  Logger.log(`Adding ${uniqueNewNotes.length} unique notes (filtered ${newNotes.length - uniqueNewNotes.length} duplicates).`);

  // Phase 3: Commit to GitHub
  const success = updateGitHubFile(
    token, owner, repo, CONFIG.FILE_PATH,
    JSON.stringify(currentData, null, 2),
    `Add ${uniqueNewNotes.length} note(s) from email`,
    currentFile ? currentFile.sha : null
  );

  // Phase 4: Only label threads after successful commit
  if (success) {
    Logger.log(`Successfully added ${uniqueNewNotes.length} notes to GitHub.`);
    for (const thread of threadsToLabel) {
      thread.addLabel(processedLabel);
      thread.markRead();
    }
    Logger.log(`Labeled ${threadsToLabel.length} threads as processed.`);
  } else {
    Logger.log('Failed to update GitHub file. Emails left unlabeled for retry.');
  }
}

function getGitHubFile(token, owner, repo, path) {
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;

  const options = {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github.v3+json'
    },
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);

  if (response.getResponseCode() === 200) {
    return JSON.parse(response.getContentText());
  } else if (response.getResponseCode() === 404) {
    return null; // File doesn't exist yet
  } else {
    Logger.log('GitHub GET error: ' + response.getContentText());
    return null;
  }
}

function updateGitHubFile(token, owner, repo, path, content, message, sha) {
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;

  const payload = {
    message: message,
    content: Utilities.base64Encode(content),
    branch: CONFIG.BRANCH
  };

  if (sha) {
    payload.sha = sha;
  }

  const options = {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github.v3+json',
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);

  if (response.getResponseCode() === 200 || response.getResponseCode() === 201) {
    return true;
  } else {
    Logger.log('GitHub PUT error: ' + response.getContentText());
    return false;
  }
}

// Manual test function - run this to test without waiting 5 mins
function testProcessEmails() {
  processNewEmails();
}
