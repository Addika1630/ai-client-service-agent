#!/usr/bin/env python3
"""
Debug environment variable loading
"""

import os
from dotenv import load_dotenv

print("🔍 Loading .env file...")
load_dotenv()

print(f"JIRA_URL: {os.getenv('JIRA_URL', 'NOT FOUND')}")
print(f"JIRA_USERNAME: {os.getenv('JIRA_USERNAME', 'NOT FOUND')}")
print(f"JIRA_API_TOKEN: {os.getenv('JIRA_API_TOKEN', 'NOT FOUND')}")
print(f"JIRA_PROJECT_KEY: {os.getenv('JIRA_PROJECT_KEY', 'NOT FOUND')}")

print("\n✅ Environment variables loaded successfully!")
