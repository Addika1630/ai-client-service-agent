#!/bin/bash
# Cleanup script for AI Agent - remove unnecessary files and code

echo "🧹 Cleaning up unnecessary files..."

# Remove calendar-related files (no longer needed for Jira ticket system)
echo "Removing calendar service files..."
rm -f calendar_service.py
rm -f credentials_sales.json
rm -f credentials_technical.json
rm -f token_sales.json
rm -f token_technical.json

# Remove unnecessary Python files
echo "Removing unnecessary Python files..."
rm -f app.py
rm -f simple_ui.py
rm -f trial.py
rm -f POC.ipynb

# Remove demo and test files
echo "Removing demo and test files..."
rm -f demo.py
rm -f test_agent.py

# Remove other unnecessary files
echo "Removing other unnecessary files..."
rm -f front-end.html
rm -f start.sh

echo "✅ File cleanup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Run: python app1.py"
echo "2. Open: http://localhost:5000"
echo ""
echo "🗂️ Remaining essential files:"
echo "- app1.py (main application)"
echo "- src/ (source code)"
echo "- requirements.txt (dependencies)"
echo "- templates/ (HTML templates)"
echo "- .env (environment variables)"
