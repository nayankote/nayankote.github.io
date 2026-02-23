#!/usr/bin/env python3
"""
Simple Markdown to HTML converter for blog posts.
Converts a markdown file to HTML using the blog-post-template.html
"""

import re
import sys
from pathlib import Path


def parse_metadata(content):
    """Extract title, date, and tag from markdown content."""
    lines = content.strip().split('\n')

    # Extract title (first line starting with #)
    title = None
    for line in lines:
        if line.startswith('# '):
            title = line[2:].strip()
            break

    # Extract publish date
    date = None
    for line in lines:
        if line.startswith('Publish date:'):
            date = line.replace('Publish date:', '').strip()
            break

    # Extract tag
    tag = None
    for line in lines:
        if line.startswith('Tag:'):
            tag = line.replace('Tag:', '').strip()
            break

    return title, date, tag


def markdown_to_html(content, img_folder=None):
    """Convert markdown content to HTML."""
    # Remove metadata lines
    lines = content.strip().split('\n')
    filtered_lines = []
    skip_count = 0

    for line in lines:
        if line.startswith('# ') and skip_count == 0:
            skip_count += 1
            continue
        elif line.startswith('Publish date:') or line.startswith('Tag:'):
            continue
        elif line.strip() == '' and skip_count == 1:
            skip_count += 1
            continue
        else:
            filtered_lines.append(line)

    content = '\n'.join(filtered_lines)

    # Convert images ![alt](path) to <img> tags
    def replace_image(match):
        alt = match.group(1)
        path = match.group(2)
        # Decode URL-encoded paths and use the img_folder path
        from urllib.parse import unquote
        decoded_path = unquote(path)
        # Extract just the filename
        filename = decoded_path.split('/')[-1]
        if img_folder:
            img_path = f"/assets/img/{img_folder}/{filename}"
        else:
            img_path = f"/assets/img/{filename}"
        return f'<img src="{img_path}" alt="{alt}" class="blog-image">'

    content = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_image, content)

    # Convert headers (h2, h3, etc.)
    content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)

    # Convert bold **text**
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)

    # Convert italic *text*
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)

    # Convert inline code `text`
    content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)

    # Convert lists and group consecutive images
    html_lines = []
    in_list = False
    image_buffer = []

    def flush_images():
        """Output buffered images, grouping consecutive ones."""
        nonlocal image_buffer
        if not image_buffer:
            return
        if len(image_buffer) == 1:
            html_lines.append(image_buffer[0])
        elif len(image_buffer) == 2:
            html_lines.append('<div class="image-grid">')
            html_lines.extend(image_buffer)
            html_lines.append('</div>')
        else:  # 3 or more
            html_lines.append('<div class="image-grid three-up">')
            html_lines.extend(image_buffer)
            html_lines.append('</div>')
        image_buffer = []

    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        is_image = line.strip().startswith('<img ')

        if line.strip().startswith('- '):
            flush_images()
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{line.strip()[2:]}</li>')
        elif is_image:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            image_buffer.append(line.strip())
        elif line.strip() == '' and image_buffer:
            # Check if next non-empty line is also an image
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines) and lines[j].strip().startswith('<img '):
                # Skip blank line, next image will be added to buffer
                pass
            else:
                flush_images()
        else:
            flush_images()
            if in_list:
                html_lines.append('</ul>')
                in_list = False

            # Convert paragraphs
            if line.strip() and not line.strip().startswith('<'):
                html_lines.append(f'<p>{line.strip()}</p>')
            elif line.strip().startswith('<'):
                html_lines.append(line)
            else:
                html_lines.append('')
        i += 1

    flush_images()
    if in_list:
        html_lines.append('</ul>')

    return '\n'.join(html_lines)


def create_blog_post(md_file, output_file=None):
    """Convert markdown file to HTML blog post."""
    # Read markdown file
    md_path = Path(md_file)
    if not md_path.exists():
        print(f"Error: File {md_file} not found")
        return

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Parse metadata
    title, date, tag = parse_metadata(md_content)

    if not title or not date:
        print("Error: Could not extract title or date from markdown")
        return

    # Generate img folder name from title
    img_folder = title.replace(' ', '-').replace(':', '-').replace('.', '')
    img_folder = re.sub(r'-+', '-', img_folder)

    # Convert markdown to HTML
    html_content = markdown_to_html(md_content, img_folder)

    # Read template
    template_path = Path(md_path.parent) / 'blog-post-template.html'
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Replace placeholders
    template = template.replace('Your Blog Title Here', title)
    template = template.replace('Month Day, Year', date)
    template = template.replace('<!-- Your blog content here -->', html_content)

    # Determine output filename
    if output_file is None:
        # Generate filename from title
        filename = title.replace(' ', '-').replace(':', '-').replace('.', '')
        filename = re.sub(r'-+', '-', filename)  # Remove multiple dashes
        output_file = md_path.parent / f"{filename}.html"
    else:
        output_file = Path(output_file)

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(template)

    print(f"✓ Created: {output_file}")
    print(f"  Title: {title}")
    print(f"  Date: {date}")
    print(f"  Tag: {tag}")

    return output_file


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python convert_blog.py <markdown_file> [output_file]")
        sys.exit(1)

    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    create_blog_post(md_file, output_file)
