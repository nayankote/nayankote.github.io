#!/bin/bash

# Personal Website Publishing Script
# This script automates the entire workflow from Ghost to GitHub Pages

set -e  # Exit on any error

# Configuration
GHOST_DIR="../personal_website_ghost"
SITE_DIR="."
SITE_URL="https://nayankote.com"
GITHUB_REPO="origin main"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists gssg; then
        print_error "gssg (Ghost Static Site Generator) is not installed"
        print_status "Install it with: npm install -g ghost-static-site-generator"
        exit 1
    fi
    
    if ! command_exists git; then
        print_error "Git is not installed"
        exit 1
    fi
    
    if [ ! -d "$GHOST_DIR" ]; then
        print_error "Ghost directory not found at $GHOST_DIR"
        print_status "Make sure you're running this script from the personal website directory"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Generate static site from Ghost
generate_site() {
    print_status "Generating static site from Ghost..."
    
    cd "$GHOST_DIR"
    
    if ! gssg --url "$SITE_URL" --dest "$SITE_DIR"; then
        print_error "Failed to generate static site"
        exit 1
    fi
    
    cd "$SITE_DIR"
    print_success "Static site generated"
}

# Fix localhost links in generated files
fix_localhost_links() {
    print_status "Fixing localhost links..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        find . -name "*.html" -exec sed -i '' "s|http://localhost:2368|$SITE_URL|g" {} \;
    else
        # Linux
        find . -name "*.html" -exec sed -i "s|http://localhost:2368|$SITE_URL|g" {} \;
    fi
    
    print_success "Localhost links fixed"
}

# Remove generated content directory (gssg bug)
remove_content_dir() {
    print_status "Removing generated content directory..."
    
    if [ -d "./content" ]; then
        rm -rf ./content
        print_success "Content directory removed"
    else
        print_warning "Content directory not found (already removed or not created)"
    fi
}

# Organize blog posts into /blogs/ folder
organize_blog_posts() {
    print_status "Organizing blog posts into /blogs/ folder..."
    
    # Create blogs directory if it doesn't exist
    mkdir -p blogs
    
    # Define folders that should NOT be moved to blogs/
    exclude_folders=("blogs" "blog" "about" "projects" "404" "rss" "tag" "author" "public" "assets" ".git")
    
    # Find all directories in the current folder
    for folder in */; do
        if [ -d "$folder" ]; then
            # Remove trailing slash
            folder_name="${folder%/}"
            
            # Check if this folder should be excluded
            should_exclude=false
            for exclude in "${exclude_folders[@]}"; do
                if [ "$folder_name" = "$exclude" ]; then
                    should_exclude=true
                    break
                fi
            done
            
            # If not excluded, it's likely a blog post
            if [ "$should_exclude" = false ]; then
                if [ ! -d "blogs/$folder_name" ]; then
                    mv "$folder_name" blogs/
                    print_status "Moved $folder_name to blogs/"
                else
                    print_warning "$folder_name already exists in blogs/ directory"
                fi
            fi
        fi
    done
    
    print_success "Blog posts organized"
}

# Clean up unnecessary files
cleanup_files() {
    print_status "Cleaning up unnecessary files..."
    
    # Remove files that are generated each time and shouldn't be in the final site
    files_to_remove=(
        "content"      # gssg bug - generated each time
        ".DS_Store"    # macOS system file - generated each time
    )
    
    for file in "${files_to_remove[@]}"; do
        if [ -e "$file" ]; then
            if [ -d "$file" ]; then
                rm -rf "$file"
            else
                rm "$file"
            fi
            print_status "Removed $file"
        fi
    done
    
    print_success "Cleanup completed"
}

# Git operations
git_operations() {
    print_status "Performing Git operations..."
    
    # Check if there are changes to commit
    if git diff-index --quiet HEAD --; then
        print_warning "No changes to commit"
        return
    fi
    
    # Add all changes
    git add .
    
    # Get current timestamp for commit message
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Commit changes
    git commit -m "Auto-publish: Update site at $timestamp"
    
    # Push to GitHub
    print_status "Pushing to GitHub..."
    if git push $GITHUB_REPO; then
        print_success "Successfully pushed to GitHub"
    else
        print_error "Failed to push to GitHub"
        print_status "You may need to enter your SSH passphrase or check your Git credentials"
        exit 1
    fi
}

# Main execution
main() {
    print_status "Starting publishing process..."
    print_status "Site URL: $SITE_URL"
    print_status "Ghost directory: $GHOST_DIR"
    print_status "Site directory: $SITE_DIR"
    echo
    
    # Run all steps
    check_prerequisites
    generate_site
    fix_localhost_links
    remove_content_dir
    organize_blog_posts
    cleanup_files
    git_operations
    
    echo
    print_success "🎉 Publishing complete! Your site should be live in a few minutes."
    print_status "Visit: $SITE_URL"
}

# Run main function
main "$@" 