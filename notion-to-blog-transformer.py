#!/usr/bin/env python3
"""
Notion to Blog Post Transformer
Automatically converts Notion HTML exports to properly formatted blog posts
"""

import re
import os
import sys
from datetime import datetime
from bs4 import BeautifulSoup
import argparse

class NotionBlogTransformer:
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
    
    def extract_notion_content(self, notion_html_path):
        """Extract content from Notion HTML export"""
        try:
            with open(notion_html_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1', class_='post-title')
            if not title_elem:
                title_elem = soup.find('h1', class_='page-title')
            if not title_elem:
                title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Untitled Blog Post"
            
            # Extract publish date
            date_elem = soup.find('time')
            if not date_elem:
                # Look for meta tag with publish date
                date_elem = soup.find('meta', property='article:published_time')
                if date_elem:
                    publish_date = date_elem.get('content')
                else:
                    publish_date = datetime.now().isoformat()
            else:
                publish_date = date_elem.get('datetime') if date_elem else datetime.now().isoformat()
            
            # Extract tags
            tag_elem = soup.find('span', class_='selected-value')
            tag_name = tag_elem.get_text().strip() if tag_elem else None
            tag_slug = tag_name.lower().replace(' ', '-') if tag_name else None
            
            # Extract main content
            content_elem = soup.find('section', class_='post-content')
            if not content_elem:
                content_elem = soup.find('div', class_='page-body')
            if not content_elem:
                content_elem = soup.find('article')
            
            if content_elem:
                # Clean up the content
                content = self.clean_notion_content(content_elem)
            else:
                content = "<p>Content not found</p>"
            
            return {
                'title': title,
                'publish_date': publish_date,
                'tag_name': tag_name,
                'tag_slug': tag_slug,
                'content': content
            }
            
        except Exception as e:
            print(f"Error reading Notion HTML: {e}")
            sys.exit(1)
    
    def clean_notion_content(self, content_elem):
        """Clean and format Notion content"""
        # Remove Notion-specific classes and styling
        for elem in content_elem.find_all(class_=True):
            elem.attrs = {}
        
        # Convert Notion images to proper format
        for img in content_elem.find_all('img'):
            src = img.get('src', '')
            if src.startswith('attachment:'):
                # Extract filename from attachment
                filename = src.split(':')[-1]
                img['src'] = f"/assets/img/{filename}"
            elif not src.startswith('/'):
                # If it's a relative path, make it absolute
                img['src'] = f"/assets/img/{src}"
            
            # Add alt text if missing
            if not img.get('alt'):
                img['alt'] = "Blog image"
        
        # Convert Notion links to proper format
        for link in content_elem.find_all('a'):
            href = link.get('href', '')
            if href.startswith('attachment:'):
                # Remove attachment links
                link.unwrap()
            elif href.startswith('http'):
                # External links - add target="_blank"
                link['target'] = '_blank'
                link['rel'] = 'noopener'
        
        # Clean up empty elements
        for elem in content_elem.find_all():
            if elem.get_text().strip() == '' and not elem.find_all():
                elem.decompose()
        
        return str(content_elem)
    
    def generate_blog_post(self, notion_data, output_path=None):
        """Generate the final blog post using the template"""
        # Format dates
        try:
            publish_date = datetime.fromisoformat(notion_data['publish_date'].replace('Z', '+00:00'))
            publish_date_formatted = publish_date.strftime('%d %b %Y')
            publish_date_iso = publish_date.isoformat()
        except:
            publish_date_formatted = "Today"
            publish_date_iso = datetime.now().isoformat()
        
        # Generate canonical URL
        title_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', notion_data['title']).lower().replace(' ', '-')
        canonical_url = f"https://nayankote.com/blogs/{title_slug}/"
        
        # Generate description (first 160 characters of content)
        content_text = re.sub(r'<[^>]+>', '', notion_data['content'])
        description = content_text[:160] + "..." if len(content_text) > 160 else content_text
        
        # Replace template variables
        blog_post = self.template.replace('Your Blog Title Here', notion_data['title'])
        blog_post = blog_post.replace('Month Day, Year', publish_date_formatted)
        blog_post = blog_post.replace('<!-- Your blog content here -->', notion_data['content'])
        
        # Tags are not used in this template, so we skip tag handling
        
        # Generate output filename
        if not output_path:
            safe_title = re.sub(r'[^a-zA-Z0-9\s-]', '', notion_data['title'])
            output_path = f"blogs/{safe_title}.html"
        
        return blog_post, output_path
    
    def transform(self, notion_html_path, output_path=None):
        """Main transformation function"""
        print(f"🔄 Transforming Notion HTML: {notion_html_path}")
        
        # Extract content from Notion HTML
        notion_data = self.extract_notion_content(notion_html_path)
        print(f"✅ Extracted: {notion_data['title']}")
        
        # Generate blog post
        blog_post, final_output_path = self.generate_blog_post(notion_data, output_path)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
        
        # Write the transformed blog post
        with open(final_output_path, 'w', encoding='utf-8') as f:
            f.write(blog_post)
        
        print(f"✅ Blog post generated: {final_output_path}")
        print(f"📝 Title: {notion_data['title']}")
        print(f"📅 Date: {notion_data['publish_date']}")
        if notion_data['tag_name']:
            print(f"🏷️  Tag: {notion_data['tag_name']}")
        
        return final_output_path

def main():
    parser = argparse.ArgumentParser(description='Transform Notion HTML exports to blog posts')
    parser.add_argument('notion_html', help='Path to Notion HTML export file')
    parser.add_argument('-o', '--output', help='Output path for the blog post')
    parser.add_argument('-t', '--template', default='blogs/blog-post-template.html', help='Path to blog template')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.notion_html):
        print(f"Error: Input file '{args.notion_html}' not found!")
        sys.exit(1)
    
    # Initialize transformer
    transformer = NotionBlogTransformer(args.template)
    
    # Transform the blog post
    output_path = transformer.transform(args.notion_html, args.output)
    
    print(f"\n🎉 Transformation complete!")
    print(f"📁 Output: {output_path}")
    print(f"\n📋 Next steps:")
    print(f"1. Review the generated blog post")
    print(f"2. Update index.html files to include the new post")
    print(f"3. Add any images to /assets/img/ folder")
    print(f"4. Commit and push to git")

if __name__ == "__main__":
    main()
