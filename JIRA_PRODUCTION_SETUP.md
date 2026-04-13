# Production Jira Integration Setup

## 🚀 Overview
This guide helps you set up the production Jira integration for your AI Agent, replacing the demo version with real Jira API functionality.

## 📋 Prerequisites

### 1. Jira Instance Requirements
- Jira Cloud or Jira Server/Data Center with REST API access
- Appropriate permissions to create issues and read project data
- API token for authentication

### 2. Required Environment Variables
Update your `.env` file with the following variables:

```bash
# Jira Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=YOURPROJECT
```

## 🔧 Setup Instructions

### Step 1: Get Jira API Token

1. **Log in to Atlassian Account**
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens

2. **Create API Token**
   - Click "Create API token"
   - Enter a label (e.g., "AI Agent Integration")
   - Click "Create"
   - Copy the token immediately (you won't see it again)

3. **Add Token to .env**
   - Add the copied token to your `JIRA_API_TOKEN` environment variable

### Step 2: Get Project Information

1. **Find your Jira URL**
   - For Jira Cloud: `https://your-domain.atlassian.net`
   - For Jira Server: `https://your-jira-server.com`

2. **Find your Project Key**
   - Go to your Jira project
   - The project key is in the URL (e.g., `PROJ` in `https://domain.atlassian.net/browse/PROJ-123`)

3. **Verify Permissions**
   - Ensure your account can:
     - Create issues in the target project
     - Read project metadata
     - Search for users (if using reporter email)

### Step 3: Run Setup Script

Execute the setup script in Git Bash:

```bash
cd /d/R_and_D-project/ai-client-service-agent
bash setup_production.sh
```

Or manually:

```bash
# Install requests library
pip install requests

# Replace demo with production version
cp src/jira_tool_production.py src/jira_tool.py
rm -f src/jira_tool_production.py
```

### Step 4: Test the Integration

1. **Start the Application**
   ```bash
   python app1.py
   ```

2. **Open the Web Interface**
   - Navigate to `http://localhost:5000`

3. **Test Ticket Creation**
   - Try creating a test ticket with the AI Agent
   - Check if the ticket appears in your Jira project

## 🛠️ Production Features

### Real Jira API Integration
- **Ticket Creation**: Creates actual tickets in your Jira instance
- **User Lookup**: Finds users by email for reporter assignment
- **Priority Mapping**: Maps priorities to Jira standards
- **Issue Type Validation**: Validates issue types against project configuration
- **Error Handling**: Comprehensive error reporting from Jira API

### Supported Issue Types
- Task
- Bug
- Story
- Epic
- Sub-task

### Supported Priorities
- Low → Low
- Medium → Medium
- High → High
- Critical → Highest

### Error Handling
- Network connectivity issues
- Authentication failures
- Permission errors
- Invalid project configuration
- Missing required fields

## 🔍 Troubleshooting

### Common Issues

#### 1. "Missing required Jira environment variables"
**Solution**: Ensure all four environment variables are set in your `.env` file.

#### 2. "Failed to connect to Jira"
**Solution**: 
- Verify `JIRA_URL` is correct
- Check network connectivity
- Ensure Jira instance is accessible

#### 3. "Jira API Error: 401 Unauthorized"
**Solution**:
- Verify `JIRA_USERNAME` and `JIRA_API_TOKEN`
- Ensure API token is valid and not expired
- Check if user has necessary permissions

#### 4. "Jira API Error: 404 Not Found"
**Solution**:
- Verify `JIRA_PROJECT_KEY` is correct
- Ensure project exists and is accessible
- Check if project key case matches exactly

#### 5. "Ticket not found or access denied"
**Solution**:
- Verify ticket ID format (e.g., "PROJ-123")
- Ensure user has permission to view the ticket
- Check if ticket exists in the project

### Debug Mode
To enable debug logging, add this to your `.env` file:

```bash
DEBUG=true
```

## 📊 Monitoring

### Ticket Creation Success Metrics
- Monitor ticket creation success rates
- Track error types and frequencies
- Monitor response times

### Jira API Limits
- Be aware of Jira API rate limits
- Implement throttling if needed for high volume
- Monitor API usage in your Atlassian account

## 🔒 Security Considerations

### API Token Security
- Store API tokens securely in environment variables
- Never commit API tokens to version control
- Rotate tokens regularly
- Use least-privilege principle for user permissions

### Network Security
- Use HTTPS for all Jira communications
- Consider VPN or private network for Jira Server
- Implement IP whitelisting if supported

## 🚀 Advanced Configuration

### Custom Fields
To support custom Jira fields, modify the `create_ticket` method in `jira_tool.py`:

```python
# Add custom fields to issue_payload
issue_payload["fields"]["customfield_10010"] = "Custom Value"
```

### Workflow Customization
- Modify issue type mapping for custom workflows
- Add custom priority levels
- Implement custom status transitions

### Integration with Other Systems
- Extend to create tickets in multiple projects
- Add integration with service desk systems
- Implement ticket escalation workflows

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all environment variables are correct
3. Test Jira API access with tools like Postman
4. Review Jira system logs for additional error details

## 🔄 Updates and Maintenance

- Regularly update the `requests` library
- Monitor Jira API changes and deprecations
- Test integration after Jira updates
- Keep API tokens fresh and secure
