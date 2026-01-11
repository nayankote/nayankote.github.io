#!/usr/bin/env python3
"""
Script to reorganize and fix the CSS file for standardization.
This adds proper navigation styles and blog content styles while preserving other CSS.
"""

import re

# Read the minified CSS
with open('assets/css/style.css', 'r') as f:
    css_content = f.read()

# The new, correct navigation and base styles from the homepage
CORRECT_BASE_STYLES = '''
/* ============================================
   SECTION 1: COLOR VARIABLES & THEME SYSTEM
   Ground truth - used on ALL pages
   ============================================ */

:root {
    --color-bg: #fff;
    --color-text: #181818;
    --color-accent: #4a5568;
    --color-nav-bg: #fff;
    --color-nav-text: #181818;
}

@media (prefers-color-scheme: dark) {
    :root {
        --color-bg: #181818;
        --color-text: #fff;
        --color-accent: #a0aec0;
        --color-nav-bg: #181818;
        --color-nav-text: #fff;
    }
}

html.theme-dark {
    --color-bg: #181818;
    --color-text: #fff;
    --color-accent: #a0aec0;
    --color-nav-bg: #181818;
    --color-nav-text: #fff;
}

html.theme-light {
    --color-bg: #fff;
    --color-text: #181818;
    --color-accent: #4a5568;
    --color-nav-bg: #fff;
    --color-nav-text: #181818;
}

/* ============================================
   SECTION 2: NAVIGATION STYLES
   Ground truth navigation - matches homepage
   ============================================ */

body {
    background: var(--color-bg);
    color: var(--color-text);
    font-size: 1.2em;
    font-family: 'Fira Sans', 'Segoe UI', Arial, sans-serif;
    margin: 0;
}

.nav-header {
    background: var(--color-nav-bg);
    color: var(--color-nav-text);
    padding: 16px 32px;
    box-sizing: border-box;
}

.nav-wrapper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 650px;
    margin: 0 auto;
    padding: 0;
}

.nav-wrapper ul {
    margin: 0;
    padding: 0;
    display: flex;
    gap: 16px;
    list-style: none;
}

.nav-wrapper ul li {
    list-style: none;
}

.nav-wrapper ul li a {
    color: var(--color-nav-text);
    font-weight: 600;
    text-decoration: none;
    font-size: 0.95em;
    padding: 8px 16px;
    border: 2px solid var(--color-accent);
    border-radius: 6px;
    display: inline-block;
    transition: all 0.2s ease;
    background: transparent;
}

.nav-wrapper ul li a:hover {
    background: var(--color-accent);
    color: var(--color-bg);
}

.nav-wrapper ul li.active a {
    background: var(--color-accent);
    color: var(--color-bg);
}

/* Theme toggle button - matches homepage */
#theme-toggle {
    margin-left: auto;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border: 1px solid var(--color-accent);
    border-radius: 20px;
    color: var(--color-nav-text);
    text-decoration: none;
    font-size: 0.9em;
    transition: all 0.2s ease;
    cursor: pointer;
}

#theme-toggle:hover {
    background: var(--color-accent);
    color: var(--color-bg);
}

#theme-toggle svg {
    transition: transform 0.3s ease;
}

#theme-toggle:hover svg {
    transform: rotate(20deg);
}

/* ============================================
   SECTION 3: BLOG CONTENT STYLES
   Used on individual blog posts
   ============================================ */

.homepage-container {
    max-width: 720px;
    margin: 0 auto;
    padding: 80px 32px 0 32px;
}

.blog-content-container {
    max-width: 650px;
    margin: 0 auto;
    padding: 32px 32px 48px 32px;
    border: 1px solid rgba(74, 85, 104, 0.2);
    border-radius: 12px;
    box-shadow: 0 0 0 1px rgba(74, 85, 104, 0.1),
        0 4px 16px rgba(0, 0, 0, 0.05);
    background: linear-gradient(to bottom,
            rgba(74, 85, 104, 0.02) 0%,
            transparent 100%);
}

html.theme-dark .blog-content-container {
    border: 1px solid rgba(160, 174, 192, 0.2);
    box-shadow: 0 0 0 1px rgba(160, 174, 192, 0.1),
        0 4px 16px rgba(0, 0, 0, 0.3);
    background: linear-gradient(to bottom,
            rgba(160, 174, 192, 0.03) 0%,
            transparent 100%);
}

.blog-title-main {
    font-size: 2em;
    font-weight: 700;
    color: var(--color-accent);
    margin-bottom: 24px;
}

.blog-date-main {
    color: var(--color-accent);
    font-size: 1em;
    margin-bottom: 32px;
    display: block;
}

.back-button {
    display: inline-block;
    margin-bottom: 32px;
    color: var(--color-text);
    text-decoration: none;
    font-weight: 400;
    font-size: 0.9em;
    transition: color 0.2s;
}

.back-button:hover {
    color: var(--color-accent);
}

.blog-content-container p {
    margin-bottom: 1.2em;
    line-height: 1.6;
    font-family: 'Libre Baskerville', serif;
}

.blog-content-container ul,
.blog-content-container ol {
    margin-left: 1.5em;
    margin-bottom: 1.2em;
    font-family: 'Libre Baskerville', serif;
}

.blog-content-container li {
    margin-bottom: 0.5em;
}

.blog-content-container h1,
.blog-content-container h2,
.blog-content-container h3,
.blog-content-container h4,
.blog-content-container h5,
.blog-content-container h6 {
    margin-top: 2em;
    margin-bottom: 1em;
    color: var(--color-text);
}

.blog-content-container h2 {
    font-size: 1.5em;
    font-weight: 600;
}

.blog-content-container h3 {
    font-size: 1.3em;
    font-weight: 600;
}

.blog-content-container blockquote {
    border-left: 4px solid var(--color-accent);
    margin: 1.5em 0;
    padding: 0.5em 1em;
    color: var(--color-accent);
    background: rgba(74, 85, 104, 0.05);
    font-style: italic;
}

html.theme-dark .blog-content-container blockquote {
    background: rgba(160, 174, 192, 0.1);
}

.blog-content-container figure,
.blog-content-container .image {
    margin: 2em 0;
    text-align: center;
}

.blog-content-container figure img,
.blog-content-container .image img,
.blog-content-container img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.blog-content-container a {
    color: var(--color-accent);
    text-decoration: underline;
}

.blog-content-container a:hover {
    text-decoration: none;
}

.blog-content-container code {
    background: rgba(74, 85, 104, 0.1);
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 0.9em;
}

html.theme-dark .blog-content-container code {
    background: rgba(160, 174, 192, 0.2);
}

.blog-content-container pre {
    background: rgba(74, 85, 104, 0.05);
    padding: 1em;
    border-radius: 8px;
    overflow-x: auto;
    margin: 1.5em 0;
}

html.theme-dark .blog-content-container pre {
    background: rgba(160, 174, 192, 0.1);
}

.blog-content-container pre code {
    background: none;
    padding: 0;
}

/* ============================================
   SECTION 4: NOTES-SPECIFIC STYLES
   Used only on notes page
   ============================================ */

#graph-container {
    width: 100vw;
    height: calc(100vh - 57px);
    position: relative;
    background: var(--color-bg);
}

.node {
    cursor: pointer;
}

.node circle {
    stroke: var(--color-bg);
    stroke-width: 2px;
}

.node text {
    font-size: 11px;
    font-weight: 600;
    fill: var(--color-text);
    pointer-events: none;
    text-anchor: middle;
    font-family: 'Fira Sans', sans-serif;
}

.link {
    stroke: var(--color-accent);
    stroke-opacity: 0.2;
    stroke-width: 1px;
}

.link.strong {
    stroke-width: 2px;
    stroke-opacity: 0.3;
}

.link.highlighted {
    stroke: var(--color-accent);
    stroke-opacity: 0.5;
    stroke-width: 2px;
}

.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
}

.modal-content {
    background: var(--color-bg);
    margin: 8vh auto;
    padding: 32px;
    border: 2px solid var(--color-accent);
    border-radius: 6px;
    width: 90%;
    max-width: 650px;
    max-height: 80vh;
    overflow-y: auto;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 16px;
}

.modal-title {
    font-size: 1.5em;
    font-weight: 700;
    color: var(--color-text);
}

.close {
    color: var(--color-accent);
    font-size: 28px;
    font-weight: 300;
    cursor: pointer;
}

.modal-metadata {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
}

.modal-date {
    font-size: 0.9em;
    color: var(--color-accent);
    font-weight: 600;
}

.modal-tags {
    display: flex;
    gap: 6px;
}

.tag {
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75em;
    font-weight: 600;
    color: white;
}

.modal-text {
    line-height: 1.7;
    color: var(--color-text);
    font-size: 0.95em;
}

.message {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    max-width: 600px;
    padding: 40px;
}

.message h3 {
    font-size: 1.3em;
    margin-bottom: 20px;
}

.message p {
    margin: 10px 0;
    line-height: 1.6;
}

.controls-overlay {
    position: absolute;
    top: 20px;
    right: 20px;
    display: flex;
    gap: 8px;
    z-index: 10;
}

.control-btn {
    background: var(--color-bg);
    border: 2px solid var(--color-accent);
    color: var(--color-text);
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 0.85em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: 'Fira Sans', sans-serif;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.control-btn:hover {
    background: var(--color-accent);
    color: var(--color-bg);
}

/* Responsive adjustments */
@media (max-width: 900px) {
    .homepage-container,
    .nav-header,
    .nav-wrapper,
    .blog-content-container {
        max-width: 100%;
        padding-left: 12px;
        padding-right: 12px;
    }
}

/* ============================================
   SECTION 5: EXISTING STYLES FROM ORIGINAL
   Preserved from the original style.css
   ============================================ */

'''

# Find where the old :root declaration starts (after normalize.css)
# We'll insert our new styles right after the font-face declarations

# Split at the first :root declaration
parts = css_content.split(':root{', 1)
if len(parts) == 2:
    before_root = parts[0]
    # Remove old conflicting nav-header styles from the rest
    after_root = ':root{' + parts[1]

    # Remove problematic old navigation styles
    # We'll use regex to remove specific conflicting rules

    # Remove old .nav-header a styles (these are wrong)
    after_root = re.sub(
        r'\.nav-header a\{[^}]*\}',
        '',
        after_root
    )

    # Remove old .nav-header li styles that conflict
    after_root = re.sub(
        r'\.nav-header li\{[^}]*margin-right:3rem[^}]*\}',
        '',
        after_root
    )

    # Remove old .nav-header ul styles
    after_root = re.sub(
        r'\.nav-header ul\{[^}]*width:100%[^}]*\}',
        '',
        after_root
    )

    # Now write the new file
    new_css = before_root + CORRECT_BASE_STYLES + after_root

    with open('assets/css/style-new.css', 'w') as f:
        f.write(new_css)

    print("✓ Created new style-new.css with proper organization")
    print("✓ Added correct navigation styles")
    print("✓ Added blog content styles")
    print("✓ Added notes-specific styles")
    print("✓ Removed conflicting old navigation styles")
else:
    print("ERROR: Could not find :root declaration in CSS")
