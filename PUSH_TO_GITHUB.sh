#!/bin/bash
# Script to push FinanceY to GitHub

set -e

echo "🚀 Pushing FinanceY to GitHub..."
echo ""

# Check if .git exists
if [ ! -d .git ]; then
    echo "⚠️  Git repository not initialized. Initializing..."
    git init
    echo "✅ Git repository initialized"
fi

# Check if .env exists
if [ -f .env ]; then
    echo "✅ .env file found - will be excluded from git (as per .gitignore)"
    if git ls-files --error-unmatch .env > /dev/null 2>&1; then
        echo "⚠️  WARNING: .env is tracked in git! Removing..."
        git rm --cached .env
    fi
else
    echo "ℹ️  No .env file found (this is okay)"
fi

# Check if remote exists
if git remote get-url origin > /dev/null 2>&1; then
    REMOTE_URL=$(git remote get-url origin)
    echo "✅ Remote already configured: $REMOTE_URL"
    read -p "Do you want to change the remote URL? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter new GitHub repository URL: " NEW_URL
        git remote set-url origin "$NEW_URL"
        echo "✅ Remote URL updated"
    fi
else
    echo "📝 Setting up GitHub remote..."
    echo ""
    echo "Please provide your GitHub repository URL:"
    echo "  Example: https://github.com/username/financey.git"
    echo "  Or SSH: git@github.com:username/financey.git"
    echo ""
    read -p "GitHub repository URL: " REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        echo "❌ No URL provided. Exiting."
        exit 1
    fi
    
    git remote add origin "$REPO_URL"
    echo "✅ Remote added: $REPO_URL"
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
echo ""
echo "Current branch: $CURRENT_BRANCH"

# Add all files
echo ""
echo "📦 Adding files to git..."
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "ℹ️  No changes to commit. Everything is up to date."
    read -p "Do you want to push anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting."
        exit 0
    fi
else
    echo "✅ Files staged"
    
    # Show what will be committed
    echo ""
    echo "Files to be committed:"
    git diff --cached --name-status | head -20
    if [ $(git diff --cached --name-status | wc -l) -gt 20 ]; then
        echo "... and more"
    fi
    
    echo ""
    read -p "Enter commit message (or press Enter for default): " COMMIT_MSG
    
    if [ -z "$COMMIT_MSG" ]; then
        COMMIT_MSG="Initial commit: FinanceY - AI-powered financial document analysis"
    fi
    
    # Commit
    echo ""
    echo "💾 Creating commit..."
    git commit -m "$COMMIT_MSG"
    echo "✅ Commit created"
fi

# Set branch to main if not already
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo ""
    echo "📌 Renaming branch to 'main'..."
    git branch -M main
    CURRENT_BRANCH="main"
fi

# Push to GitHub
echo ""
echo "🚀 Pushing to GitHub..."
echo ""

# Check if branch exists on remote
if git ls-remote --heads origin "$CURRENT_BRANCH" | grep -q "$CURRENT_BRANCH"; then
    echo "⚠️  Branch '$CURRENT_BRANCH' already exists on remote"
    read -p "Pull changes first? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📥 Pulling changes..."
        git pull origin "$CURRENT_BRANCH" --no-rebase || {
            echo "⚠️  Pull failed. You may need to resolve conflicts manually."
            exit 1
        }
    fi
    git push origin "$CURRENT_BRANCH"
else
    echo "📤 Pushing new branch '$CURRENT_BRANCH'..."
    git push -u origin "$CURRENT_BRANCH"
fi

echo ""
echo "✅ Successfully pushed to GitHub!"
echo ""
echo "📍 Repository: $(git remote get-url origin)"
echo "📍 Branch: $CURRENT_BRANCH"
echo ""
echo "📝 Next steps:"
echo "   1. Visit your repository on GitHub"
echo "   2. Verify that .env is NOT in the repository"
echo "   3. Verify that .env.example IS in the repository"
echo "   4. Add repository description and topics"
echo "   5. Set up branch protection rules (optional)"
echo ""

