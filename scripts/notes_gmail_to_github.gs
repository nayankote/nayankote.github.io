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
 * The script will then run every 5 minutes automatically.
 */

const CONFIG = {
  FILE_PATH: 'notes/notes_raw.json',
  BRANCH: 'main'
};

function setup() {
  // Remove any existing triggers first
  const triggers = ScriptApp.getProjectTriggers();
  for (const trigger of triggers) {
    ScriptApp.deleteTrigger(trigger);
  }

  // Create time-based trigger to run every 5 minutes
  ScriptApp.newTrigger('processNewEmails')
    .timeBased()
    .everyMinutes(5)
    .create();

  Logger.log('Trigger created! Script will run every 5 minutes.');
  Logger.log('You can close this tab now.');
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

  // Only process emails with subject starting with "note:" or "n:"
  const threads = GmailApp.search('subject:(note: OR n:)', 0, 10);

  if (threads.length === 0) {
    Logger.log('No new emails.');
    return;
  }

  const newNotes = [];

  for (const thread of threads) {
    const messages = thread.getMessages();

    for (const message of messages) {
      if (!message.isStarred()) {  // Use star to mark as processed
        let subject = message.getSubject();
        const body = message.getPlainBody().trim();

        // Strip the note:/n: prefix from subject
        subject = subject.replace(/^(note:|n:)\s*/i, '').trim();

        // Prefer body, fall back to subject (without prefix)
        let noteText = body || subject;

        // Truncate to 200 chars as per spec
        if (noteText.length > 200) {
          noteText = noteText.substring(0, 197) + '...';
        }

        if (noteText) {
          newNotes.push({
            id: Utilities.getUuid(),
            text: noteText,
            timestamp: message.getDate().toISOString(),
            source: 'email'
          });
        }

        message.star();  // Mark as processed
      }
    }
  }

  if (newNotes.length === 0) {
    Logger.log('No new notes found.');
    return;
  }

  Logger.log(`Found ${newNotes.length} new notes.`);

  // Get current file from GitHub
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

  // Append new notes
  currentData.notes = currentData.notes.concat(newNotes);

  // Commit to GitHub
  const success = updateGitHubFile(
    token, owner, repo, CONFIG.FILE_PATH,
    JSON.stringify(currentData, null, 2),
    `Add ${newNotes.length} note(s) from email`,
    currentFile ? currentFile.sha : null
  );

  if (success) {
    Logger.log(`Successfully added ${newNotes.length} notes to GitHub.`);
  } else {
    Logger.log('Failed to update GitHub file.');
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
