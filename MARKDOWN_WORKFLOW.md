# How to Write Blog Posts (Markdown Workflow)

We have moved from a Notion-based workflow to a Markdown-based workflow for better control and simplicity.

## The Workflow

1.  **Write**: Create a Markdown file in the `drafts/` folder.
2.  **Convert**: Run the `markdown_transformer.py` script.
3.  **Publish**: Commit and push the generated HTML in `blogs/`.

## 1. Directory Structure

```
/drafts          <-- Your workspace. Put .md files here.
/blogs           <-- The output. HTML files are generated here.
/assets/img      <-- Put images here (e.g. /assets/img/my-post/image.png)
```

## 2. Writing a Post

### Option A: Write Directly in Markdown
Create a new file in `drafts/`, for example `drafts/my-new-post.md`.

### Option B: Write in Notion & Export
1.  Write your post in Notion.
2.  Click `...` (top right) > `Export`.
3.  Select **Markdown & CSV**.
4.  Unzip the download.
5.  **Ignore the CSV files** (they are just for databases).
6.  Copy the `.md` file to `drafts/`.
7.  Copy any images to `assets/img/`.

### Frontmatter (Metadata)
**Crucial Step:** Open your `.md` file and add this to the very top:

```markdown
---
title: "My Awesome Blog Post"
date: "2025-11-30"
slug: "my-awesome-post"  # Optional: overrides the filename
---
```

### Content
Write standard Markdown below the frontmatter.

```markdown
# Introduction
This is a paragraph.

## Subheading
- List item 1
- List item 2

[Link to Google](https://google.com)
![My Image](/assets/img/my-post/image.png)
```

## 3. Generating the HTML

Open your terminal (in VS Code) and run:

```bash
# Make sure your virtual environment is active
source .venv/bin/activate

# Run the transformer
python markdown_transformer.py
```

This script will:
1.  Read every `.md` file in `drafts/`.
2.  Convert it to HTML.
3.  Inject it into `blogs/blog-post-template.html`.
4.  Save the result to `blogs/`.

## 4. Publishing

Once you are happy with the generated HTML (you can open the file in `blogs/` with your browser to check):

```bash
git add .
git commit -m "New post: My Awesome Post"
git push origin main
```
