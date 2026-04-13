#!/bin/bash
# Cleanup script for AI Agent project - remove unnecessary files

echo "🧹 Cleaning up unnecessary files..."

# Remove calendar-related files (no longer needed for Jira system)
echo "📅 Removing calendar service files..."
rm -f calendar_service.py
rm -f credentials_sales.json
rm -f credentials_technical.json
rm -f token_sales.json
rm -f token_technical.json

# Remove unnecessary Python files
echo "🐍 Removing unnecessary Python files..."
rm -f app.py
rm -f simple_ui.py
rm -f trial.py
rm -f POC.ipynb

# Remove demo and test files
echo "🧪 Removing demo and test files..."
rm -f demo.py
rm -f test_agent.py

# Remove other unnecessary files
echo "🗑️ Removing other unnecessary files..."
rm -f front-end.html
rm -f start.sh
rm -f cleanup_complete.sh
rm -f setup_production.sh

# Clean Python cache files
echo "🧹 Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📁 Remaining essential files:"
echo "📄 app1.py - Main application"
echo "📁 src/ - Source code"
echo "📄 requirements.txt - Dependencies"
echo "📄 .env - Environment variables"
echo "📄 .gitignore - Git ignore file"
echo "📄 LICENSE - License file"
echo "📄 README.md - Documentation"
echo "📁 templates/ - HTML templates"
echo ""
echo "🚀 To run your AI Agent:"
echo "   python app1.py"
echo ""
echo "🌐 Open: http://localhost:5000"
