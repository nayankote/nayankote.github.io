import os
import json
import requests
from jinja2 import Template
from datetime import datetime

# Ghost API configuration
GHOST_URL = "https://nayankote.com"
API_KEY = ""  # You'll need to add your Ghost API key here

def get_posts():
    """Fetch posts from Ghost API"""
    headers = {'Authorization': f'Ghost {API_KEY}'}
    response = requests.get(f"{GHOST_URL}/ghost/api/v3/content/posts/", headers=headers)
    return response.json()['posts']

def get_pages():
    """Fetch pages from Ghost API"""
    headers = {'Authorization': f'Ghost {API_KEY}'}
    response = requests.get(f"{GHOST_URL}/ghost/api/v3/content/pages/", headers=headers)
    return response.json()['pages']

def create_html_file(content, template, output_path):
    """Create an HTML file from content and template"""
    html = template.render(content=content)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)

def main():
    # Create output directory
    os.makedirs('static', exist_ok=True)
    
    # Load templates
    with open('templates/post.html', 'r') as f:
        post_template = Template(f.read())
    
    with open('templates/page.html', 'r') as f:
        page_template = Template(f.read())
    
    with open('templates/index.html', 'r') as f:
        index_template = Template(f.read())
    
    # Get content from Ghost
    posts = get_posts()
    pages = get_pages()
    
    # Create post files
    for post in posts:
        slug = post['slug']
        create_html_file(post, post_template, f'static/posts/{slug}/index.html')
    
    # Create page files
    for page in pages:
        slug = page['slug']
        create_html_file(page, page_template, f'static/{slug}/index.html')
    
    # Create index file
    create_html_file({'posts': posts}, index_template, 'static/index.html')
    
    # Copy assets
    os.system('cp -r assets static/')

if __name__ == "__main__":
    main() 