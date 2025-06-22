# Personal Website - nayankote.com

A minimal, static personal blog built with Ghost and deployed to GitHub Pages.

## Overview

This is a static website generated from a Ghost blog and hosted on GitHub Pages. The site features a clean, minimal design with a homepage and blog section organized under `/blogs/`.

## Local Development

To work on this site locally, you'll need to set up a Ghost instance:

1. **Install Node.js** (version 18.x recommended for Ghost compatibility):
   ```bash
   nvm install 18
   nvm use 18
   ```

2. **Install Ghost CLI**:
   ```bash
   npm install -g ghost-cli
   ```

3. **Set up Ghost locally** (in a separate directory):
   ```bash
   mkdir personal_website_ghost
   cd personal_website_ghost
   ghost install local
   ```

4. **Access Ghost Admin**:
   - Open http://localhost:2368/ghost
   - Create your account and add content

## Publishing to GitHub Pages

To publish updates to the live site:

1. **Generate static files** from your local Ghost instance:
   ```bash
   cd personal_website_ghost
   gssg --url https://nayankote.com --dest ../personal\ website
   ```

2. **Fix localhost links** (required due to gssg limitation):
   ```bash
   cd ../personal\ website
   find . -name "*.html" -exec sed -i '' 's|http://localhost:2368|https://nayankote.com|g' {} \;
   ```

3. **Remove generated content directory** (gssg creates this incorrectly):
   ```bash
   rm -rf ./content
   ```

4. **Organize blog posts** (manual step for clean URLs):
   ```bash
   mkdir -p blogs
   mv welcome-to-my-blog hello-world sample-post blog-test-1 blogs/
   ```

5. **Commit and push** to GitHub:
   ```bash
   git add .
   git commit -m "Update site"
   git push origin main
   ```

## File Structure

- `index.html` - Homepage
- `blog/` - Blog listing page
- `blogs/` - Individual blog posts
  - `welcome-to-my-blog/` - Welcome post
  - `hello-world/` - Hello world post
  - `sample-post/` - Sample post
  - `blog-test-1/` - Test post
- `about/` - About page
- `projects/` - Projects page
- `assets/css/main.css` - Main stylesheet
- `routes.yaml` - Ghost routing configuration

## URL Structure

- **Homepage**: `nayankote.com/`
- **Blog listing**: `nayankote.com/blog/`
- **Individual posts**: `nayankote.com/blogs/post-slug/`
- **About**: `nayankote.com/about/`
- **Projects**: `nayankote.com/projects/`

## Theme

The site uses a custom minimal theme built for Ghost. Key features:
- Clean, typography-focused design
- Responsive layout
- Minimal navigation
- Optimized for readability

## Notes

- The `gssg` tool has some limitations that require manual fixes (localhost links, content directory)
- Blog posts are manually organized under `/blogs/` for cleaner URL structure
- All content is managed through the Ghost admin interface
- The site is completely static and hosted on GitHub Pages for free 