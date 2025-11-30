#!/usr/bin/env python3
"""
Markdown to Blog Post Transformer
Converts a single Markdown file to an HTML blog post.
Usage: python markdown_transformer.py <input_file> <output_file>
"""

import os
import sys
import argparse
import markdown
import frontmatter
from datetime import datetime
import re

class MarkdownBlogTransformer:
    def __init__(self, template_path="blogs/blog-post-template.html"):
        self.template_path = template_path
        self.template = self.load_template()

    def load_template(self):
        """Load the blog template"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Template file '{self.template_path}' not found!")
            sys.exit(1)

    def convert(self, input_path, output_path):
        """Convert a single markdown file to HTML"""
        print(f"Converting {input_path} -> {output_path}...")
        
        if not os.path.exists(input_path):
            print(f"Error: Input file '{input_path}' not found.")
            sys.exit(1)

        # Parse Frontmatter and Markdown
        with open(input_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        metadata = post.metadata
        content = post.content
        
        # Remove the first H1 heading if it exists (to avoid duplication with template title)
        # This handles Notion exports which include the title as an H1
        lines = content.split('\n')
        filtered_lines = []
        found_first_h1 = False
        
        for line in lines:
            # Check if this is an H1 heading (starts with # but not ##)
            if line.strip().startswith('# ') and not line.strip().startswith('## ') and not found_first_h1:
                found_first_h1 = True
                continue  # Skip this line
            filtered_lines.append(line)
        
        content = '\n'.join(filtered_lines)
        
        # Convert Markdown to HTML
        html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
        
        # Format date
        date_str = str(metadata.get('date', datetime.now().date()))
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%B %d, %Y')
        except ValueError:
            formatted_date = date_str

        # Inject into template
        blog_html = self.template
        blog_html = blog_html.replace('Your Blog Title Here', metadata.get('title', 'Untitled'))
        blog_html = blog_html.replace('Month Day, Year', formatted_date)
        blog_html = blog_html.replace('<!-- Your blog content here -->', html_content)
        
        # Update <title> tag
        blog_html = re.sub(r'<title>.*?</title>', f'<title>{metadata.get("title", "Untitled")}</title>', blog_html)
        
        # Write to file
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(blog_html)
        
        print(f"Success! Generated {output_path}")
        
        # Update index files
        self.update_blog_indices(metadata, output_path)

    def update_blog_indices(self, metadata, output_path):
        """Append the new post to the top of the list in index.html and blogs/index.html"""
        files_to_update = ["index.html", "blogs/index.html"]
        
        # Extract filename for the link
        filename = os.path.basename(output_path)
        link_href = f"/blogs/{filename}"
        
        # Format date
        date_str = str(metadata.get('date', datetime.now().date()))
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%b %Y')
        except ValueError:
            formatted_date = date_str

        title = metadata.get('title', 'Untitled')
        
        # Create new list item
        new_item = f"""
                <li class="blog-item">
                    <a href="{link_href}" class="blog-title">{title}</a>
                    <span class="blog-date">{formatted_date}</span>
                </li>"""

        for index_path in files_to_update:
            if not os.path.exists(index_path):
                print(f"Warning: {index_path} not found. Skipping.")
                continue

            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for duplicates
            if link_href in content:
                print(f"Skipping {index_path}: Entry for {filename} already exists.")
                continue

            # Insert at the top of the list (after <ul class="blog-list">)
            # We use a specific regex to find the FIRST occurrence of the list
            # This works for index.html because "Blogs" is the first list
            pattern = re.compile(r'(<ul class="blog-list">)')
            
            if pattern.search(content):
                # Replace the first occurrence only
                new_content = pattern.sub(r'\1' + new_item, content, count=1)
                
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Added '{title}' to {index_path}")
            else:
                print(f"Warning: Could not find <ul class='blog-list'> in {index_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Markdown to HTML blog post")
    parser.add_argument("input", help="Path to input Markdown file")
    parser.add_argument("output", help="Path to output HTML file")
    
    args = parser.parse_args()
    
    transformer = MarkdownBlogTransformer()
    transformer.convert(args.input, args.output)
