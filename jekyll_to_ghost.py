import json
import os
from datetime import datetime

# --- Configuration ---
JEKYLL_POSTS_DIR = '_posts'
GHOST_JSON_OUTPUT_FILE = 'ghost_import.json'
# -------------------

def parse_jekyll_post(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, None 

    front_matter_str = parts[1]
    body_md = parts[2].strip()

    front_matter = {}
    for line in front_matter_str.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            front_matter[key.strip()] = value.strip()
            
    # Extract date from filename, as it's more reliable
    filename = os.path.basename(file_path)
    date_str = '-'.join(filename.split('-')[:3])
    
    # Create slug from the rest of the filename
    slug = '-'.join(filename.split('-')[3:]).replace('.md', '')

    return {
        'title': front_matter.get('title', 'Untitled'),
        'slug': slug,
        'markdown': body_md,
        'published_at': datetime.strptime(date_str, '%Y-%m-%d').isoformat() + '.000Z',
        'status': 'published'
    }

def create_ghost_import_file():
    posts = []
    for filename in os.listdir(JEKYLL_POSTS_DIR):
        if filename.endswith('.md'):
            file_path = os.path.join(JEKYLL_POSTS_DIR, filename)
            post_data = parse_jekyll_post(file_path)
            if post_data:
                posts.append(post_data)

    ghost_data = {
        "meta": {
            "exported_on": int(datetime.now().timestamp() * 1000),
            "version": "5.8.0" # Example Ghost version
        },
        "data": {
            "posts": posts
        }
    }

    with open(GHOST_JSON_OUTPUT_FILE, 'w') as f:
        json.dump(ghost_data, f, indent=2)

    print(f"Successfully created Ghost import file: {GHOST_JSON_OUTPUT_FILE}")

if __name__ == '__main__':
    create_ghost_import_file() 