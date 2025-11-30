#!/usr/bin/env python3
"""
Markdown to Blog Post Transformer
Converts Markdown files with Frontmatter to HTML blog posts using a template.
"""

import os
import sys
import markdown
import frontmatter
from datetime import datetime
import re

class MarkdownBlogTransformer:
    def __init__(self, template_path="blogs/blog-post-template.html", drafts_dir="drafts", output_dir="blogs"):
        self.template_path = template_path
        self.drafts_dir = drafts_dir
        self.output_dir = output_dir
        self.template = self.load_template()

    def load_template(self):
        """Load the blog template"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Template file '{self.template_path}' not found!")
            sys.exit(1)

    def process_all(self):
        """Process all markdown files in the drafts directory"""
        if not os.path.exists(self.drafts_dir):
            print(f"Drafts directory '{self.drafts_dir}' not found.")
            return

        for filename in os.listdir(self.drafts_dir):
            if filename.endswith(".md"):
                self.process_file(os.path.join(self.drafts_dir, filename))

    def process_file(self, filepath):
        """Process a single markdown file"""
        print(f"Processing {filepath}...")
        
        # Parse Frontmatter and Markdown
        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        metadata = post.metadata
        content = post.content
        
        # Convert Markdown to HTML
        html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
        
        # Generate output filename
        if 'slug' in metadata:
            slug = metadata['slug']
        else:
            # Generate slug from title
            slug = re.sub(r'[^a-zA-Z0-9\s-]', '', metadata.get('title', 'untitled'))
            slug = re.sub(r'\s+', '-', slug.strip()).lower()
        
        output_filename = f"{slug}.html"
        output_path = os.path.join(self.output_dir, output_filename)
        
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
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(blog_html)
        
        print(f"Generated {output_path}")

if __name__ == "__main__":
    transformer = MarkdownBlogTransformer()
    transformer.process_all()
