# GitHub Setup Guide

This guide will help you push FinanceY to GitHub.

## Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Create a new repository named `financey` (or any name you prefer)
3. **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click "Create repository"

## Step 2: Push to GitHub

Run these commands in your terminal:

```bash
# Navigate to project directory
cd /Users/smehtesham/Desktop/AIProject

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: FinanceY - AI-powered financial document analysis"

# Add GitHub remote (replace YOUR_USERNAME and REPO_NAME with your actual values)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Or if using SSH:
# git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Verify

After pushing, verify that:
- ✅ `.env` file is NOT in the repository (check GitHub web interface)
- ✅ `.env.example` IS in the repository
- ✅ All source code files are present
- ✅ Documentation files (README.md, DOCKER.md, etc.) are present

## Important Security Notes

### ✅ Files that ARE committed:
- Source code
- Configuration templates (`.env.example`)
- Documentation
- Docker files
- Requirements files

### ❌ Files that are NEVER committed (in .gitignore):
- `.env` - Contains your OpenAI API key
- `data/` - Contains uploaded documents and vector stores
- `node_modules/` - Dependencies (can be reinstalled)
- `__pycache__/` - Python cache files
- `*.log` - Log files
- `*.db`, `*.sqlite` - Database files

## After Pushing to GitHub

### For Other Developers

Other developers who clone the repository should:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/REPO_NAME.git
   cd REPO_NAME
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Install dependencies:**
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend (if needed)
   cd frontend-react
   npm install
   ```

4. **Run the application:**
   ```bash
   # Using Docker (recommended)
   docker-compose up -d
   
   # Or manually
   uvicorn backend.main:app --reload
   streamlit run frontend/app.py
   ```

## GitHub Actions

The repository includes a GitHub Actions workflow (`.github/workflows/docker.yml`) that:
- Builds Docker images on push
- Tests Docker builds
- Validates docker-compose configurations

To enable GitHub Actions:
1. Push to GitHub
2. Go to your repository → Actions tab
3. Enable GitHub Actions if prompted

## Public vs Private Repository

### Public Repository
- ✅ Free
- ✅ Visible to everyone
- ⚠️ Make sure `.env` is in `.gitignore`
- ⚠️ Don't commit sensitive data

### Private Repository
- ✅ More secure
- ✅ Only you and collaborators can see it
- ⚠️ Requires GitHub Pro for advanced features (or free for personal use)
- ✅ Recommended for production projects

## Adding a License

If you want to add a license:

```bash
# Add MIT License (recommended for open source)
curl -o LICENSE https://raw.githubusercontent.com/licenses/license-templates/master/templates/mit.txt

# Edit LICENSE and replace [year] and [fullname]
# Then commit:
git add LICENSE
git commit -m "Add MIT License"
git push
```

## Creating Releases

To create a GitHub release:

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Choose a tag (e.g., `v1.0.0`)
4. Add release notes
5. Publish release

Or use the command line:

```bash
# Tag the current commit
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tags
git push origin v1.0.0
```

## Troubleshooting

### "Repository not found" error
- Check that the repository name is correct
- Verify you have access to the repository
- Check your GitHub authentication

### "Permission denied" error
- Set up SSH keys or use HTTPS with personal access token
- See: https://docs.github.com/en/authentication

### "Files too large" error
- Large files should be in `.gitignore`
- Use Git LFS for large files if needed
- See: https://git-lfs.github.com/

### Accidentally committed `.env`
If you accidentally committed `.env`:

```bash
# Remove from git (but keep local file)
git rm --cached .env

# Commit the removal
git commit -m "Remove .env from repository"

# Push the change
git push

# If already pushed, consider:
# 1. Rotating your API keys
# 2. Using git filter-branch or BFG Repo-Cleaner to remove from history
```

## Next Steps

After pushing to GitHub:

1. ✅ Update README.md with repository URL
2. ✅ Add repository description and topics on GitHub
3. ✅ Set up GitHub Actions (already configured)
4. ✅ Add collaborators if needed
5. ✅ Set up branch protection rules (Settings → Branches)
6. ✅ Enable Dependabot for security updates

## Repository Badges

You can add badges to your README.md:

```markdown
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
```

## Support

For issues with GitHub:
- GitHub Docs: https://docs.github.com
- Git documentation: https://git-scm.com/doc

