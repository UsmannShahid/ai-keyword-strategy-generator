# Security Guidelines

## API Key Security

### ✅ Current Security Status
Your OpenAI API key is properly secured:
- ✅ `.env` file is in `.gitignore` and not tracked by git
- ✅ No environment files found in git history
- ✅ API key is loaded from environment variables in code
- ✅ Proper `.env.example` template provided

### 🔒 Security Checklist

#### Git Security
- [x] `.env` file is in `.gitignore`
- [x] No API keys in source code
- [x] No API keys in git history
- [x] `.env.example` template provided (without real keys)

#### Environment Variables
- [x] API key stored in `.env` file
- [x] Application loads from `os.getenv()`
- [x] Graceful handling when API key is missing

#### Additional Security Patterns
```python
# ✅ Good: Load from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ❌ Bad: Hardcoded in source
OPENAI_API_KEY = "sk-proj-actual-key-here"
```

### 🚨 Emergency Response

#### If API Key is Accidentally Exposed
1. **Immediately revoke** the exposed key at https://platform.openai.com/api-keys
2. **Generate a new** API key
3. **Update your `.env`** file with the new key
4. **Check git history** for any commits containing the key:
   ```bash
   git log -p --all | grep -i "sk-proj"
   ```
5. **If found in git history**, consider using tools like BFG Repo-Cleaner

#### Repository Security
```bash
# Check for accidentally committed secrets
git log --all --full-history -- .env
git log -p --all | grep -E "(sk-|api.?key|secret|password)"

# Verify .env is ignored
git check-ignore .env  # Should return: .env
```

### 📋 Best Practices

#### Development
1. **Never commit** `.env` files
2. **Use `.env.example`** as a template
3. **Rotate API keys** regularly
4. **Use different keys** for development/production
5. **Monitor API usage** for unexpected activity

#### Team Collaboration
1. **Share `.env.example`** (not `.env`)
2. **Document required variables** in README
3. **Use separate API keys** per developer
4. **Consider using secret management** tools for production

#### Production Deployment
1. **Use platform environment variables** (Heroku, Vercel, etc.)
2. **Never include `.env`** in Docker images
3. **Use secret management** services (AWS Secrets Manager, etc.)
4. **Enable API key restrictions** (IP allowlisting, usage limits)

### 🔧 Environment Setup

#### For New Developers
1. Copy the template:
   ```bash
   cp .env.example .env
   ```
2. Add your API key to `.env`:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```
3. Verify it's ignored by git:
   ```bash
   git status  # .env should not appear
   ```

#### Validation Script
```python
# Add to your app startup
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    exit(1)
elif not api_key.startswith("sk-"):
    print("⚠️  API key format may be incorrect")
elif len(api_key) < 50:
    print("⚠️  API key seems too short")
else:
    print("✅ API key loaded successfully")
```

### 📱 Platform-Specific Security

#### GitHub Actions
```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

#### Heroku
```bash
heroku config:set OPENAI_API_KEY=your_api_key_here
```

#### Vercel
```bash
vercel env add OPENAI_API_KEY
```

#### Docker
```dockerfile
# Use build args, not ENV for secrets
ARG OPENAI_API_KEY
RUN some-command-using $OPENAI_API_KEY
# Don't: ENV OPENAI_API_KEY=secret
```

### 🔍 Security Monitoring

#### Regular Checks
1. **Review git status** before commits
2. **Check API usage** on OpenAI dashboard
3. **Monitor for unexpected** API calls
4. **Audit environment files** periodically

#### Automated Checks
```bash
# Pre-commit hook to check for secrets
#!/bin/sh
if git diff --cached --name-only | grep -E "\.(env|key)$"; then
    echo "❌ Environment files detected in commit"
    exit 1
fi
```

### 📞 Support

#### If You Need Help
1. **OpenAI Security**: https://platform.openai.com/docs/guides/safety-best-practices
2. **Git Security**: https://docs.github.com/en/code-security
3. **General Security**: Follow OWASP guidelines

Remember: **When in doubt, regenerate your API key!** It's better to be safe than sorry.
