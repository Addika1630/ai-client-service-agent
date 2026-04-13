import os
import json
from datetime import datetime
from typing import Dict, Optional

class JiraTicketManager:
    """Manages Jira ticket creation and operations."""
    
    def __init__(self):
        self.jira_url = os.getenv('JIRA_URL', '')
        self.jira_username = os.getenv('JIRA_USERNAME', '')
        self.jira_api_token = os.getenv('JIRA_API_TOKEN', '')
        self.project_key = os.getenv('JIRA_PROJECT_KEY', '')
        
    def create_ticket(self, summary: str, description: str, issue_type: str = "Task", 
                     priority: str = "Medium", reporter_email: str = None) -> Dict:
        """
        Create a Jira ticket with the given details.
        
        Args:
            summary: Title/subject of the ticket
            description: Detailed description of the issue
            issue_type: Type of issue (Task, Bug, Story, etc.)
            priority: Priority level (Low, Medium, High, Critical)
            reporter_email: Email of the person creating the ticket
            
        Returns:
            Dict containing ticket creation result
        """
        try:
            # For demo purposes, we'll simulate ticket creation
            # In production, you would use the Jira REST API
            ticket_id = f"{self.project_key}-{self._generate_ticket_number()}"
            
            ticket_data = {
                "id": ticket_id,
                "summary": summary,
                "description": description,
                "issue_type": issue_type,
                "priority": priority,
                "reporter_email": reporter_email,
                "status": "Open",
                "created_date": datetime.now().isoformat(),
                "url": f"{self.jira_url}/browse/{ticket_id}"
            }
            
            # Store ticket in session for demo purposes
            # In production, this would be handled by Jira API
            return {
                "success": True,
                "ticket": ticket_data,
                "message": f"✅ Ticket created successfully! Ticket ID: {ticket_id}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ Failed to create ticket: {str(e)}"
            }
    
    def _generate_ticket_number(self) -> int:
        """Generate a mock ticket number for demo purposes."""
        import random
        return random.randint(1000, 9999)
    
    def get_ticket_status(self, ticket_id: str) -> Dict:
        """Get the status of an existing ticket."""
        # Mock implementation for demo
        return {
            "ticket_id": ticket_id,
            "status": "In Progress",
            "updated_date": datetime.now().isoformat()
        }

# Global instance
jira_manager = JiraTicketManager()

def create_jira_ticket(summary: str, description: str, issue_type: str = "Task", 
                      priority: str = "Medium", reporter_email: str = None) -> str:
    """
    Create a Jira ticket for user support requests.
    
    Args:
        summary: Brief summary of the issue (max 255 characters)
        description: Detailed description of the problem or request
        issue_type: Type of issue (Task, Bug, Story, etc.)
        priority: Priority level (Low, Medium, High, Critical)
        reporter_email: Email address of the person reporting the issue
        
    Returns:
        String message indicating success or failure
    """
    if not summary or not description:
        return "⚠️ Please provide both a summary and description to create a ticket."
    
    if len(summary) > 255:
        return "⚠️ Summary is too long. Please keep it under 255 characters."
    
    valid_types = ["Task", "Bug", "Story", "Epic", "Sub-task"]
    if issue_type not in valid_types:
        issue_type = "Task"
    
    valid_priorities = ["Low", "Medium", "High", "Critical"]
    if priority not in valid_priorities:
        priority = "Medium"
    
    result = jira_manager.create_ticket(
        summary=summary,
        description=description,
        issue_type=issue_type,
        priority=priority,
        reporter_email=reporter_email
    )
    
    if result["success"]:
        ticket = result["ticket"]
        response = f"""{result['message']}

📋 **Ticket Details:**
- **ID:** {ticket['id']}
- **Summary:** {ticket['summary']}
- **Type:** {ticket['issue_type']}
- **Priority:** {ticket['priority']}
- **Status:** {ticket['status']}
- **Created:** {ticket['created_date']}
- **URL:** {ticket['url']}

📧 You'll receive updates at: {reporter_email or 'No email provided'}

You can track your ticket status using the ticket ID: {ticket['id']}"""
        return response
    else:
        return result["message"]

def get_ticket_info(ticket_id: str) -> str:
    """Get information about an existing ticket."""
    if not ticket_id:
        return "⚠️ Please provide a ticket ID."
    
    try:
        status = jira_manager.get_ticket_status(ticket_id)
        return f"""📋 **Ticket Information:**
- **Ticket ID:** {status['ticket_id']}
- **Status:** {status['status']}
- **Last Updated:** {status['updated_date']}

You can view more details at: {jira_manager.jira_url}/browse/{ticket_id}"""
    except Exception as e:
        return f"❌ Error retrieving ticket information: {str(e)}"
