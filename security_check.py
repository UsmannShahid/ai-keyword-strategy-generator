#!/usr/bin/env python3
"""
Security check script for AI Keyword Tool
Validates that sensitive files are properly secured
"""

import os
import subprocess
import sys

def check_git_status():
    """Check if any sensitive files are tracked by git."""
    print("🔍 Checking git status...")
    
    try:
        # Check if .env is being tracked
        result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
        tracked_files = result.stdout.split('\n')
        
        sensitive_files = [f for f in tracked_files if f.endswith(('.env', '.key')) and not f.endswith('.example')]
        
        if sensitive_files:
            print(f"❌ SECURITY ISSUE: Sensitive files tracked by git: {sensitive_files}")
            return False
        else:
            print("✅ No sensitive files tracked by git")
            
        # Check if .env is properly ignored
        result = subprocess.run(['git', 'check-ignore', '.env'], capture_output=True)
        if result.returncode == 0:
            print("✅ .env file is properly ignored by git")
        else:
            print("⚠️  .env file may not be ignored by git")
            
    except FileNotFoundError:
        print("⚠️  Git not found - skipping git checks")
    
    return True

def check_env_file():
    """Check .env file security."""
    print("\n🔍 Checking .env file...")
    
    if not os.path.exists('.env'):
        print("⚠️  .env file not found")
        if os.path.exists('.env.example'):
            print("📝 .env.example found - copy it to .env and add your API key")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
    
    if 'your_openai_api_key_here' in content:
        print("⚠️  .env file contains placeholder - add your real API key")
        return False
    
    if 'OPENAI_API_KEY=sk-' in content:
        print("✅ .env file contains API key")
        return True
    else:
        print("⚠️  .env file may not contain a valid API key")
        return False

def check_source_code():
    """Check source code for hardcoded secrets."""
    print("\n🔍 Checking source code for hardcoded secrets...")
    
    python_files = ['app.py'] + [f for f in os.listdir('.') if f.endswith('.py')]
    
    for file in python_files:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encodings
                try:
                    with open(file, 'r', encoding='latin-1') as f:
                        content = f.read()
                except:
                    print(f"⚠️  Could not read {file} - skipping")
                    continue
            
            # Check for hardcoded API keys (but exclude validation code)
            if 'sk-proj-' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'sk-proj-' in line and not line.strip().startswith('#'):
                        # Check if it's an actual key (longer than 20 chars after sk-proj-)
                        import re
                        matches = re.findall(r'sk-proj-[A-Za-z0-9-_]{20,}', line)
                        if matches:
                            print(f"❌ HARDCODED API KEY FOUND in {file}:{i+1}")
                            print(f"    {line.strip()}")
            
            # Check for other suspicious patterns
            suspicious_patterns = [
                r'sk-[A-Za-z0-9]{48,}',  # OpenAI API keys
                r'OPENAI_API_KEY\s*=\s*["\']sk-',  # Direct assignment
            ]
            
            for pattern in suspicious_patterns:
                import re
                matches = re.findall(pattern, content)
                if matches:
                    print(f"⚠️  Suspicious pattern found in {file}: {pattern}")
                    for match in matches:
                        if len(match) > 20:  # Only flag if it looks like a real key
                            print(f"    {match[:20]}...")
    
    print("✅ Source code check complete")
    return True

def check_gitignore():
    """Check if .gitignore properly excludes sensitive files."""
    print("\n🔍 Checking .gitignore...")
    
    if not os.path.exists('.gitignore'):
        print("❌ .gitignore file not found")
        return False
    
    with open('.gitignore', 'r') as f:
        content = f.read()
    
    required_patterns = ['.env', 'venv/', '__pycache__/']
    missing_patterns = []
    
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"⚠️  Missing patterns in .gitignore: {missing_patterns}")
        return False
    else:
        print("✅ .gitignore properly configured")
        return True

def main():
    """Run all security checks."""
    print("🔒 AI Keyword Tool Security Check")
    print("=" * 40)
    
    checks = [
        check_git_status,
        check_env_file,
        check_source_code,
        check_gitignore
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Error in {check.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    if all(results):
        print("✅ All security checks passed!")
        return 0
    else:
        print("⚠️  Some security issues found - please review above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
