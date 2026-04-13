import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class JiraTicketManager:
    """Manages Jira ticket creation and operations using real Jira REST API."""
    
    def __init__(self):
        self.jira_url = os.getenv('JIRA_URL', '').rstrip('/')
        self.jira_username = os.getenv('JIRA_USERNAME', '')
        self.jira_api_token = os.getenv('JIRA_API_TOKEN', '')
        self.project_key = os.getenv('JIRA_PROJECT_KEY', '')
        
        # Check if required environment variables are set
        if not all([self.jira_url, self.jira_username, self.jira_api_token, self.project_key]):
            print("Warning: Missing required Jira environment variables. Please set JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN, and JIRA_PROJECT_KEY")
            self.auth = None
            self.headers = None
            return
        
        # Set up authentication
        self.auth = HTTPBasicAuth(self.jira_username, self.jira_api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
    def create_ticket(self, summary: str, description: str, issue_type: str = "Task", 
                     priority: str = "Medium", reporter_email: str = None) -> Dict:
        """
        Create a Jira ticket using the real Jira REST API.
        
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
            # Check if Jira is properly configured
            if self.auth is None:
                return {
                    "success": False,
                    "error": "Jira not configured",
                    "message": "❌ Jira integration is not properly configured. Please check your environment variables."
                }
            
            # Validate inputs
            if not summary or not description:
                return {
                    "success": False,
                    "error": "Summary and description are required",
                    "message": "❌ Please provide both a summary and description to create a ticket."
                }
            
            if len(summary) > 255:
                return {
                    "success": False,
                    "error": "Summary too long",
                    "message": "❌ Summary is too long. Please keep it under 255 characters."
                }
            
            # Map issue types and priorities to Jira standards
            issue_type_mapping = {
                "Task": "Task",
                "Bug": "Bug", 
                "Story": "Story",
                "Epic": "Epic",
                "Sub-task": "Sub-task"
            }
            
            priority_mapping = {
                "Low": "Low",
                "Medium": "Medium", 
                "High": "High",
                "Critical": "Highest"
            }
            
            jira_issue_type = issue_type_mapping.get(issue_type, "Task")
            jira_priority = priority_mapping.get(priority, "Medium")
            
            # Get project metadata to validate issue type and priority
            project_metadata = self._get_project_metadata()
            if not project_metadata:
                return {
                    "success": False,
                    "error": "Failed to connect to Jira",
                    "message": f"❌ Failed to connect to Jira at {self.jira_url}. Please check your URL, API token, and permissions."
                }
            
            # Validate issue type exists in project
            valid_issue_types = [issue['name'] for issue in project_metadata.get('issuetypes', [])]
            if jira_issue_type not in valid_issue_types:
                jira_issue_type = "Task"  # Fallback to Task
            
            # Get priority ID
            priorities = self._get_priorities()
            priority_id = None
            for p in priorities:
                if p['name'] == jira_priority:
                    priority_id = p['id']
                    break
            
            # Construct the Jira issue payload
            issue_payload = {
                "fields": {
                    "project": {
                        "key": self.project_key
                    },
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": description
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {
                        "name": jira_issue_type
                    }
                }
            }
            
            # Add priority if available
            if priority_id:
                issue_payload["fields"]["priority"] = {"id": priority_id}
            
            # Add reporter if email provided
            if reporter_email:
                # Check if user exists in Jira
                user_info = self._find_user(reporter_email)
                if user_info:
                    issue_payload["fields"]["reporter"] = {
                        "id": user_info['accountId'],
                        "displayName": user_info['displayName']
                    }
            
            # Create the issue via Jira REST API
            create_url = f"{self.jira_url}/rest/api/3/issue"
            print(f"🎫 Creating ticket at: {create_url}")
            response = requests.post(
                create_url,
                headers=self.headers,
                auth=self.auth,
                json=issue_payload,
                timeout=10
            )
            print(f"📊 Create response status: {response.status_code}")
            
            if response.status_code == 201:  # Created successfully
                issue_data = response.json()
                ticket_id = issue_data['key']
                ticket_url = f"{self.jira_url}/browse/{ticket_id}"
                
                return {
                    "success": True,
                    "ticket": {
                        "id": ticket_id,
                        "summary": summary,
                        "description": description,
                        "issue_type": jira_issue_type,
                        "priority": jira_priority,
                        "reporter_email": reporter_email,
                        "status": "Open",
                        "created_date": datetime.now().isoformat(),
                        "url": ticket_url
                    },
                    "message": f"✅ Ticket created successfully! Ticket ID: {ticket_id}"
                }
            else:
                error_msg = self._extract_error_message(response)
                return {
                    "success": False,
                    "error": f"Jira API Error: {response.status_code}",
                    "message": f"❌ Failed to create ticket: {error_msg}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": "Network error",
                "message": f"❌ Network error connecting to Jira: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Unexpected error",
                "message": f"❌ Unexpected error: {str(e)}"
            }
    
    def _get_project_metadata(self) -> Dict:
        """Get project metadata including issue types."""
        try:
            url = f"{self.jira_url}/rest/api/3/project/{self.project_key}"
            print(f"🔗 Connecting to: {url}")
            response = requests.get(url, headers=self.headers, auth=self.auth, timeout=10)
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Project access failed: {response.text}")
                return {}
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return {}
    
    def _get_priorities(self) -> list:
        """Get available priorities from Jira."""
        try:
            url = f"{self.jira_url}/rest/api/3/priority"
            response = requests.get(url, headers=self.headers, auth=self.auth)
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
    
    def _find_user(self, email: str) -> Dict:
        """Find a user by email address."""
        try:
            url = f"{self.jira_url}/rest/api/3/user/search"
            params = {"query": email}
            response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    if user.get('emailAddress', '').lower() == email.lower():
                        return user
            return {}
        except:
            return {}
    
    def _extract_error_message(self, response) -> str:
        """Extract meaningful error message from Jira API response."""
        try:
            error_data = response.json()
            if 'errors' in error_data:
                errors = []
                for error in error_data['errors']:
                    errors.append(f"{error['title']}: {error.get('detail', '')}")
                return "; ".join(errors)
            elif 'errorMessages' in error_data:
                return "; ".join(error_data['errorMessages'])
            else:
                return response.text
        except:
            return response.text
    
    def get_ticket_status(self, ticket_id: str) -> Dict:
        """Get the status of an existing ticket."""
        try:
            # Check if Jira is properly configured
            if self.auth is None:
                return {
                    "ticket_id": ticket_id,
                    "error": "Jira not configured",
                    "status": "Unknown"
                }
            
            url = f"{self.jira_url}/rest/api/3/issue/{ticket_id}?fields=status"
            response = requests.get(url, headers=self.headers, auth=self.auth)
            
            if response.status_code == 200:
                issue_data = response.json()
                status_info = issue_data['fields']['status']
                return {
                    "ticket_id": ticket_id,
                    "status": status_info['name'],
                    "status_category": status_info['statusCategory']['name'],
                    "updated_date": datetime.now().isoformat()
                }
            else:
                return {
                    "ticket_id": ticket_id,
                    "error": "Ticket not found or access denied",
                    "status": "Unknown"
                }
        except Exception as e:
            return {
                "ticket_id": ticket_id,
                "error": str(e),
                "status": "Unknown"
            }

# Global instance
jira_manager = None
try:
    jira_manager = JiraTicketManager()
    if jira_manager is None or jira_manager.auth is None:
        print("Warning: Jira integration is not properly configured. Please check your environment variables.")
except Exception as e:
    print(f"Warning: Failed to initialize JiraTicketManager: {str(e)}")
    jira_manager = None

def create_jira_ticket(summary: str, description: str, issue_type: str = "Task", 
                      priority: str = "Medium", reporter_email: str = None) -> str:
    """
    Create a Jira ticket for user support requests using real Jira API.
    
    Args:
        summary: Brief summary of the issue (max 255 characters)
        description: Detailed description of the problem or request
        issue_type: Type of issue (Task, Bug, Story, etc.)
        priority: Priority level (Low, Medium, High, Critical)
        reporter_email: Email address of the person reporting the issue
        
    Returns:
        String message indicating success or failure
    """
    if jira_manager is None:
        return "❌ Jira integration is not properly configured. Please check your environment variables."
    
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
    """Get information about an existing ticket using real Jira API."""
    if jira_manager is None:
        return "❌ Jira integration is not properly configured. Please check your environment variables."
    
    if not ticket_id:
        return "⚠️ Please provide a ticket ID."
    
    try:
        status = jira_manager.get_ticket_status(ticket_id)
        if 'error' in status:
            return f"❌ Error retrieving ticket information: {status['error']}"
        
        return f"""📋 **Ticket Information:**
- **Ticket ID:** {status['ticket_id']}
- **Status:** {status['status']}
- **Category:** {status['status_category']}
- **Last Updated:** {status['updated_date']}

You can view more details at: {jira_manager.jira_url}/browse/{ticket_id}"""
    except Exception as e:
        return f"❌ Error retrieving ticket information: {str(e)}"


