# 🔒 .gitignore Configuration Guide

## Overview

The `.gitignore` file has been configured to exclude all sensitive data, temporary files, and generated content from version control while keeping essential configuration templates.

---

## ✅ Files That ARE Ignored (Won't be committed)

### 🔐 Sensitive & Security Files
- `.env` - Production environment variables with secrets
- `.env.local`, `.env.production` - Environment-specific configs
- `credentials.json` - Google Service Account credentials
- `*-credentials.json` - Any credential files
- `service-account*.json` - Service account keys
- `*.pem`, `*.key`, `*.p12`, `*.pfx` - Private keys and certificates

### 📊 Database Files
- `db.sqlite3` - SQLite database file
- `db.sqlite3-journal` - Database journal

### 📁 Generated Directories
- `staticfiles/` - Collected static files (run `collectstatic`)
- `media/` - User uploads (resumes, attachments)
- `logs/` - Log files
- `__pycache__/` - Python bytecode cache

### 📄 Document Files
- `*.pdf` - All PDF files (resumes, reports)
- Exceptions: `!docs/*.pdf`, `!templates/*.pdf` (if these dirs exist)

### 🐍 Python Files
- `*.pyc`, `*.pyo` - Compiled Python files
- `*.egg-info/` - Package metadata
- `.Python` - Python installation files

### 💻 Virtual Environment
- `venv/` - Virtual environment directory
- `env/`, `ENV/`, `.venv` - Alternative venv names

### 🔧 IDE & Editor Files
- `.vscode/` - VS Code settings
- `.idea/` - PyCharm/IntelliJ settings
- `*.swp`, `*.swo` - Vim swap files
- `.DS_Store` - macOS Finder metadata

### 📝 Logs & Temporary Files
- `*.log` - All log files
- `*.tmp` - Temporary files
- `*.old` - Old backup files
- `*.backup`, `*.bak` - Backup files

---

## ✅ Files That ARE NOT Ignored (Will be committed)

### 📋 Essential Templates
- `.env.example` - Environment variable template (no secrets)
- `.gitignore` - This ignore file itself

### 📦 Configuration Files
- `requirements.txt` - Python dependencies
- `gunicorn_config.py` - Production server config
- `deploy.sh` - Deployment script
- `start_server.sh` - Server start script

### 🐍 Python Source Code
- `*.py` - All Python source files
- `manage.py` - Django management script

### 🌐 Django Project Files
- `linkedin_scraper/settings.py` - Django settings
- `linkedin_scraper/urls.py` - URL configuration
- `linkedin_scraper/wsgi.py` - WSGI application

### 📁 Static Files (Source)
- `scraper/static/` - Original static files (CSS, JS)
- `scraper/templates/` - Django templates

### 📖 Documentation
- `*.md` - All Markdown documentation files
- `README.md` - Project readme

---

## 🔍 Testing .gitignore

### Check if a file is ignored:
```bash
git check-ignore -v filename

# Examples:
git check-ignore -v .env          # Should show: .gitignore:39:.env
git check-ignore -v credentials.json  # Should show: .gitignore:52:credentials.json
git check-ignore -v .env.example  # Should show: (no output - NOT ignored)
```

### See what files would be added:
```bash
git status --ignored

# Or just see untracked files:
git status --short
```

### Test before committing:
```bash
# Dry-run to see what would be added
git add --dry-run .

# Check if sensitive files are listed
git status
```

---

## ⚠️ Critical Files to NEVER Commit

| File | Contains | Risk if Exposed |
|------|----------|-----------------|
| `.env` | API keys, passwords, secrets | **CRITICAL** - Full system compromise |
| `credentials.json` | Google service account keys | **CRITICAL** - Access to Google Sheets, data theft |
| `db.sqlite3` | Database with emails, phones | **HIGH** - Privacy breach, GDPR violation |
| `*.pdf` (resumes) | Personal information | **HIGH** - Privacy violation |
| `*.pem`, `*.key` | SSL certificates, private keys | **CRITICAL** - MITM attacks, impersonation |

**If you accidentally commit sensitive files:**
```bash
# Remove from git but keep locally
git rm --cached filename

# Remove from history (USE WITH CAUTION!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch filename" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (only if absolutely necessary)
git push origin --force --all
```

---

## 📋 .gitignore Structure

```gitignore
# Python
__pycache__/
*.py[cod]
venv/

# Django
*.log
db.sqlite3
/staticfiles
/media

# Environment variables (Keep .env.example!)
.env
.env.*
!.env.example

# Credentials (NEVER commit!)
credentials.json
*.pem
*.key

# Resume files
*.pdf
!docs/*.pdf

# IDE
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.old
*.backup
```

---

## 🔧 Maintenance

### Adding new patterns:
```bash
# Edit .gitignore
nano .gitignore

# Add pattern, e.g.:
echo "new-secret-file.txt" >> .gitignore

# Commit the change
git add .gitignore
git commit -m "Update gitignore"
```

### If you need to force-add an ignored file:
```bash
# Add specific ignored file (use rarely!)
git add -f filename
```

### Clear git cache after updating .gitignore:
```bash
# Remove all files from git cache
git rm -r --cached .

# Re-add everything (respecting new .gitignore)
git add .

# Commit
git commit -m "Clean up tracked files per .gitignore"
```

---

## ✅ Pre-Commit Checklist

Before committing, verify:

- [ ] `.env` is NOT in `git status`
- [ ] `credentials.json` is NOT in `git status`
- [ ] `db.sqlite3` is NOT in `git status`
- [ ] `*.pdf` files are NOT in `git status` (except docs/templates if applicable)
- [ ] `venv/` is NOT in `git status`
- [ ] `__pycache__/` directories are NOT in `git status`
- [ ] `.env.example` IS in `git status` (should be committed)
- [ ] `requirements.txt` IS in `git status` (should be committed)

Run check:
```bash
git status | grep -E "(\.env|credentials|\.pdf|\.sqlite3|venv|__pycache__)"
# Should return nothing (except .env.example)
```

---

## 🎯 Common Scenarios

### Scenario 1: New developer setup
```bash
# They clone the repo
git clone <repo-url>

# They DON'T get:
# - .env (they must create from .env.example)
# - credentials.json (they must get from team)
# - db.sqlite3 (they run migrations to create)
# - venv/ (they create their own)

# They DO get:
# - .env.example (template to create .env)
# - requirements.txt (to install dependencies)
# - All source code
```

### Scenario 2: Deploying to production
```bash
# Push code to repo
git push origin main

# On server, sensitive files are separate:
# - .env (manually created on server)
# - credentials.json (uploaded separately)
# - db.sqlite3 (created by migrations)

# These are NEVER in git!
```

### Scenario 3: Multiple environments
```bash
# Development
.env              (ignored)
.env.example      (committed)

# Staging
.env.staging      (ignored)

# Production
.env.production   (ignored)

# Template for all
.env.example      (committed)
```

---

## 📊 Summary

| Category | Ignored | Committed |
|----------|---------|-----------|
| **Secrets** | .env, credentials.json | .env.example |
| **Database** | db.sqlite3 | migrations/ |
| **Static** | staticfiles/ | scraper/static/ |
| **Media** | media/ uploads | - |
| **Python** | __pycache__/, *.pyc | *.py source |
| **Venv** | venv/ | requirements.txt |
| **Config** | - | settings.py, gunicorn_config.py |
| **Docs** | - | *.md files |

---

## 🆘 Emergency: Committed Sensitive Data

If you accidentally committed `.env` or `credentials.json`:

### Step 1: Remove from repo immediately
```bash
git rm --cached .env credentials.json
git commit -m "Remove sensitive files"
git push
```

### Step 2: Rotate all secrets
- Generate new Django SECRET_KEY
- Regenerate Google Service Account credentials
- Change all API keys
- Update passwords

### Step 3: Clean history (if public repo)
```bash
# Remove from entire git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env credentials.json" \
  --prune-empty --tag-name-filter cat -- --all

git push origin --force --all
```

### Step 4: Verify
```bash
# Check it's gone
git log --all --full-history --source -- .env
git log --all --full-history --source -- credentials.json
```

---

## 📞 Support

- **Configuration Issue**: Check this guide
- **Accidental Commit**: Follow emergency procedure above
- **Pattern Not Working**: Test with `git check-ignore -v filename`
- **Need to Add Exception**: Use `!pattern` in .gitignore

---

**Remember**: It's easier to prevent than to clean up. Always run `git status` before committing!

---

**Last Updated**: 2025-10-20  
**Status**: ✅ Configured and Tested

