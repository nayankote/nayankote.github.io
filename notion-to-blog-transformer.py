#!/usr/bin/env python3
"""
Notion to Blog Post Transformer - Improved Version
Automatically converts Notion HTML exports to properly formatted blog posts
Enhanced with better debugging and more robust content extraction
"""

import re
import os
import sys
from datetime import datetime
from bs4 import BeautifulSoup
import argparse

class NotionBlogTransformer:
    def __init__(self, template_path="blogs/blog-post-template.html", debug=False):
        self.template_path = template_path
        self.debug = debug
        self.template = self.load_template()
    
    def debug_print(self, message):
        """Print debug messages if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG] {message}")
    
    def load_template(self):
        """Load the blog template"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Template file '{self.template_path}' not found!")
            sys.exit(1)
    
    def extract_notion_content(self, notion_html_path):
        """Extract content from Notion HTML export with improved parsing"""
        try:
            with open(notion_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                self.debug_print(f"HTML file size: {len(html_content)} characters")
                soup = BeautifulSoup(html_content, 'html.parser')
            
            # Debug: Print structure
            if self.debug:
                self.debug_structure(soup)
            
            # Extract title - try multiple methods
            title = self.extract_title(soup)
            self.debug_print(f"Extracted title: {title}")
            
            # Extract publish date
            publish_date = self.extract_date(soup)
            self.debug_print(f"Extracted date: {publish_date}")
            
            # Extract main content
            content = self.extract_content(soup)
            self.debug_print(f"Extracted content length: {len(content)} characters")
            
            return {
                'title': title,
                'publish_date': publish_date,
                'content': content
            }
            
        except Exception as e:
            print(f"Error reading Notion HTML: {e}")
            sys.exit(1)
    
    def debug_structure(self, soup):
        """Print HTML structure for debugging"""
        print("\n[DEBUG] HTML Structure Analysis:")
        
        # Check for common containers
        containers = [
            'body', 'main', 'article', '.notion-page-content',
            '.notion-page-content-inner', '.notion-selectable',
            '.page-body', '[role="main"]'
        ]
        
        for selector in containers:
            elements = soup.select(selector)
            if elements:
                print(f"  Found {len(elements)} element(s) matching '{selector}'")
                for i, elem in enumerate(elements[:2]):  # Show first 2
                    text_preview = elem.get_text()[:100].replace('\n', ' ').strip()
                    print(f"    [{i}] {text_preview}...")
        
        # Check all div classes
        divs_with_classes = soup.find_all('div', class_=True)
        print(f"\n  Found {len(divs_with_classes)} divs with classes")
        unique_classes = set()
        for div in divs_with_classes:
            unique_classes.update(div.get('class', []))
        
        notion_classes = [cls for cls in unique_classes if 'notion' in cls.lower()]
        if notion_classes:
            print(f"  Notion-related classes: {sorted(notion_classes)[:10]}...")
    
    def extract_title(self, soup):
        """Extract title from various possible locations"""
        # Try different selectors for title
        title_selectors = [
            'h1.post-title',
            'h1.page-title', 
            '.notion-page-title',
            '.notion-header-title',
            'title',  # HTML title tag
            'h1',     # Any h1
            '[data-block-type="header"]',
            '.notion-page-icon-cover + *',  # Element after cover
        ]
        
        for selector in title_selectors:
            self.debug_print(f"Trying title selector: {selector}")
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                self.debug_print(f"  Found: '{title}'")
                if title and title.lower() not in ['untitled', 'notion', '']:
                    return title
        
        # Fallback: try to find the first meaningful heading
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            title = heading.get_text().strip()
            if len(title) > 5 and title.lower() not in ['untitled', 'notion']:
                self.debug_print(f"Fallback title found: '{title}'")
                return title
        
        return "Untitled Blog Post"
    
    def extract_date(self, soup):
        """Extract date from various possible locations"""
        # Try to find date in various formats
        date_selectors = [
            'time[datetime]',
            '.notion-created-time',
            '.notion-last-edited-time',
            'meta[property="article:published_time"]',
            'meta[name="date"]',
            '[data-value*="202"]',  # Look for year patterns
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_val = date_elem.get('datetime') or date_elem.get('content') or date_elem.get('data-value') or date_elem.get_text()
                if date_val:
                    self.debug_print(f"Found date candidate: {date_val}")
                    try:
                        # Try to parse the date
                        parsed_date = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                        return parsed_date.isoformat()
                    except:
                        # Try other date formats
                        try:
                            parsed_date = datetime.strptime(date_val, '%Y-%m-%d')
                            return parsed_date.isoformat()
                        except:
                            pass
        
        return datetime.now().isoformat()
    
    def extract_content(self, soup):
        """Extract and clean main content with enhanced debugging"""
        # Try different content selectors in order of specificity
        content_selectors = [
            '.notion-page-content',
            '.notion-page-content-inner',
            'div[data-block-type]',  # Notion blocks
            '.notion-selectable.notion-page-block',
            'article',
            '.post-content',
            '.page-body',
            'main',
            '[role="main"]',
            '.notion-page-content-inner div',
            'body > div',  # Fallback to body children
        ]
        
        content_elem = None
        for selector in content_selectors:
            self.debug_print(f"Trying content selector: {selector}")
            elements = soup.select(selector)
            if elements:
                self.debug_print(f"  Found {len(elements)} elements")
                # Take the element with most text content
                best_elem = max(elements, key=lambda x: len(x.get_text()))
                text_preview = best_elem.get_text()[:100].replace('\n', ' ').strip()
                self.debug_print(f"  Best element preview: {text_preview}...")
                
                if len(best_elem.get_text().strip()) > 50:  # Must have substantial content
                    content_elem = best_elem
                    break
        
        # Ultimate fallback: get all text from body, excluding nav/header/footer
        if not content_elem:
            self.debug_print("Using body fallback")
            content_elem = soup.find('body')
            if content_elem:
                # Remove navigation, header, footer elements
                for tag in content_elem.find_all(['nav', 'header', 'footer', 'script', 'style']):
                    tag.decompose()
        
        if content_elem:
            raw_content = str(content_elem)
            self.debug_print(f"Raw content length before cleaning: {len(raw_content)}")
            cleaned_content = self.clean_notion_content(content_elem)
            self.debug_print(f"Cleaned content length: {len(cleaned_content)}")
            return cleaned_content
        else:
            self.debug_print("No content found!")
            return "<p>Content not found - check your Notion export</p>"
    
    def clean_notion_content(self, content_elem):
        """Enhanced content cleaning for Notion exports"""
        # Create a copy to avoid modifying the original
        content = BeautifulSoup(str(content_elem), 'html.parser')
        
        # Remove Notion-specific elements that shouldn't be in the blog
        notion_junk_selectors = [
            '.notion-topbar',
            '.notion-sidebar',
            '.notion-navbar',
            '.notion-breadcrumb',
            '.notion-collection-header',
            '.notion-page-icon',
            '.notion-page-cover',
            '.notion-scroller',
            'script',
            'style',
            '.notion-presence',
            '.notion-overlay-container',
            '.notion-help-button',
            '.notion-comments-button',
        ]
        
        removed_count = 0
        for selector in notion_junk_selectors:
            for elem in content.select(selector):
                elem.decompose()
                removed_count += 1
        
        self.debug_print(f"Removed {removed_count} junk elements")
        
        # Clean up class attributes (remove Notion-specific classes but preserve structure)
        for elem in content.find_all(class_=True):
            # Keep only semantic/useful classes, remove Notion-specific ones
            classes = elem.get('class', [])
            clean_classes = []
            
            for class_name in classes:
                if not any(notion_prefix in class_name for notion_prefix in 
                          ['notion-', 'notion_', 'semantic-', 'toastify']):
                    clean_classes.append(class_name)
            
            if clean_classes:
                elem['class'] = clean_classes
            else:
                del elem['class']
        
        # Clean up other Notion-specific attributes
        notion_attrs = ['data-block-id', 'data-table-id', 'data-collection-id', 
                       'data-page-links', 'spellcheck', 'placeholder', 'contenteditable',
                       'data-block-type', 'data-content-editable-leaf']
        
        attrs_removed = 0
        for elem in content.find_all():
            for attr in notion_attrs:
                if attr in elem.attrs:
                    del elem.attrs[attr]
                    attrs_removed += 1
        
        self.debug_print(f"Removed {attrs_removed} notion-specific attributes")
        
        # Process images
        self.process_images(content)
        
        # Process links
        self.process_links(content)
        
        # Process text formatting
        self.process_text_formatting(content)
        
        # Clean up empty elements
        self.remove_empty_elements(content)
        
        # Wrap images in figure tags for proper styling
        self.wrap_images_in_figures(content)
        
        # Extract only the inner content, not the wrapper
        if content.find():
            # Get the content inside the wrapper element
            inner_content = ''.join(str(child) for child in content.children)
            return inner_content
        else:
            return str(content)
    
    def process_images(self, content):
        """Process and clean image elements"""
        images_processed = 0
        for img in content.find_all('img'):
            src = img.get('src', '')
            
            # Handle different image source formats from Notion
            if src.startswith('attachment:'):
                filename = src.split(':')[-1]
                img['src'] = f"/assets/img/{filename}"
            elif src.startswith('https://www.notion.so/image/'):
                # Extract image URL from Notion's proxy
                import urllib.parse
                parsed_url = urllib.parse.urlparse(src)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if 'url' in query_params:
                    actual_url = query_params['url'][0]
                    # If it's a relative path or filename, use local assets
                    if not actual_url.startswith('http'):
                        img['src'] = f"/assets/img/{os.path.basename(actual_url)}"
                    else:
                        img['src'] = actual_url
            elif not src.startswith(('http', '/')):
                # Relative path - assume it's in assets
                img['src'] = f"/assets/img/{src}"
            
            # Ensure alt text exists
            if not img.get('alt'):
                img['alt'] = "Blog image"
            
            # Remove Notion-specific styling
            for attr in ['style', 'width', 'height']:
                if attr in img.attrs:
                    del img.attrs[attr]
            
            images_processed += 1
        
        self.debug_print(f"Processed {images_processed} images")
    
    def process_links(self, content):
        """Process and clean link elements"""
        links_processed = 0
        for link in content.find_all('a'):
            href = link.get('href', '')
            
            # Remove Notion-specific link formats
            if href.startswith('attachment:') or href.startswith('notion://'):
                link.unwrap()
                continue
            
            # Add target="_blank" for external links
            if href.startswith('http') and 'nayankote.com' not in href:
                link['target'] = '_blank'
                link['rel'] = 'noopener'
            
            # Clean up link attributes
            for attr in ['style', 'class']:
                if attr in link.attrs:
                    del link.attrs[attr]
            
            links_processed += 1
        
        self.debug_print(f"Processed {links_processed} links")
    
    def process_text_formatting(self, content):
        """Process text formatting elements"""
        # Remove empty formatting tags
        empty_removed = 0
        for tag_name in ['strong', 'em', 'u', 'del', 's', 'mark']:
            for elem in content.find_all(tag_name):
                if not elem.get_text().strip():
                    elem.unwrap()
                    empty_removed += 1
        
        self.debug_print(f"Removed {empty_removed} empty formatting tags")
    
    def wrap_images_in_figures(self, content):
        """Wrap standalone images in figure tags for consistent styling"""
        images_wrapped = 0
        for img in content.find_all('img'):
            parent = img.parent
            
            # Only wrap if not already in a figure
            if parent and parent.name != 'figure':
                # Check if image is standalone (not inline with text)
                siblings_text = ''.join(sibling.get_text() if hasattr(sibling, 'get_text') else str(sibling) 
                                      for sibling in parent.children if sibling != img).strip()
                
                if not siblings_text:  # Image is standalone
                    figure = content.new_tag('figure', class_='image')
                    img.wrap(figure)
                    images_wrapped += 1
        
        self.debug_print(f"Wrapped {images_wrapped} images in figures")
    
    def remove_empty_elements(self, content):
        """Remove empty elements that don't contribute to content"""
        # Elements that should be removed if empty
        removable_when_empty = ['p', 'div', 'span', 'strong', 'em', 'u']
        
        total_removed = 0
        changed = True
        while changed:
            changed = False
            for tag_name in removable_when_empty:
                for elem in content.find_all(tag_name):
                    if not elem.get_text().strip() and not elem.find_all(['img', 'br', 'hr']):
                        elem.decompose()
                        changed = True
                        total_removed += 1
        
        self.debug_print(f"Removed {total_removed} empty elements")
    
    def generate_blog_post(self, notion_data, output_path=None):
        """Generate the final blog post using the template"""
        # Format dates
        try:
            publish_date = datetime.fromisoformat(notion_data['publish_date'].replace('Z', '+00:00'))
            publish_date_formatted = publish_date.strftime('%B %d, %Y')
            publish_date_iso = publish_date.isoformat()
        except:
            publish_date = datetime.now()
            publish_date_formatted = publish_date.strftime('%B %d, %Y')
            publish_date_iso = publish_date.isoformat()
        
        # Generate clean title slug for filename
        title_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', notion_data['title'])
        title_slug = re.sub(r'\s+', '-', title_slug.strip()).lower()
        title_slug = re.sub(r'-+', '-', title_slug)  # Remove multiple dashes
        
        # Replace template variables with actual content
        blog_post = self.template.replace('Your Blog Title Here', notion_data['title'])
        blog_post = blog_post.replace('Month Day, Year', publish_date_formatted)
        blog_post = blog_post.replace('<!-- Your blog content here -->', notion_data['content'])
        
        # Also update the HTML title tag
        blog_post = re.sub(r'<title>.*?</title>', f'<title>{notion_data["title"]}</title>', blog_post)
        
        # Generate output filename if not provided
        if not output_path:
            output_path = f"blogs/{title_slug}.html"
        
        return blog_post, output_path
    
    def transform(self, notion_html_path, output_path=None):
        """Main transformation function"""
        print(f"Transforming Notion HTML: {notion_html_path}")
        
        # Extract content from Notion HTML
        notion_data = self.extract_notion_content(notion_html_path)
        print(f"Extracted: {notion_data['title']}")
        
        # Generate blog post
        blog_post, final_output_path = self.generate_blog_post(notion_data, output_path)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(final_output_path) if os.path.dirname(final_output_path) else '.', exist_ok=True)
        
        # Write the transformed blog post
        with open(final_output_path, 'w', encoding='utf-8') as f:
            f.write(blog_post)
        
        print(f"Blog post generated: {final_output_path}")
        print(f"Title: {notion_data['title']}")
        print(f"Date: {notion_data['publish_date']}")
        
        return final_output_path

def main():
    parser = argparse.ArgumentParser(description='Transform Notion HTML exports to blog posts')
    parser.add_argument('notion_html', help='Path to Notion HTML export file')
    parser.add_argument('-o', '--output', help='Output path for the blog post')
    parser.add_argument('-t', '--template', default='blogs/blog-post-template.html', help='Path to blog template')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.notion_html):
        print(f"Error: Input file '{args.notion_html}' not found!")
        sys.exit(1)
    
    # Initialize transformer
    transformer = NotionBlogTransformer(args.template, debug=args.debug)
    
    # Transform the blog post
    try:
        output_path = transformer.transform(args.notion_html, args.output)
        
        print(f"\nTransformation complete!")
        print(f"Output: {output_path}")
        print(f"\nNext steps:")
        print(f"1. Review the generated blog post")
        print(f"2. Update index.html files to include the new post")
        print(f"3. Add any images to /assets/img/ folder")
        print(f"4. Commit and push to git")
        
    except Exception as e:
        print(f"Error during transformation: {e}")
        import traceback
        if args.debug:
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()