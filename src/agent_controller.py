from llama_index.core.agent import FunctionCallingAgent
from llama_index.core.tools import FunctionTool
from src.generators import Generators
from src.tools import *
from src.utils.app_logger import GenericLogger
from src.faq_pdf_tool import query_faq_pdf

logger = GenericLogger().get_logger()

# Create all the function tools
greet_user_tool = FunctionTool.from_defaults(fn=greet_user_and_ask_name)

meet_tool = FunctionTool.from_defaults(
    fn=schedule_google_meet,
    name="schedule_google_meet",
    description="Schedule a Google Meet meeting. Provide date (YYYY-MM-DD), time (HH:MM), subject, and optionally duration. This function will automatically check if the time slot is available before scheduling."
)

# Create the FAQ tool from PDF documents
faq_pdf_tool = FunctionTool.from_defaults(
    fn=query_faq_pdf,
    name="faq_pdf_tool",
    description="Answer company FAQs from PDF files."
)

availability_tool = FunctionTool.from_defaults(
    fn=get_calendar_availability,
    name="get_calendar_availability",
    description="Check available time slots for a specific date. Provide date (YYYY-MM-DD) and optional duration in minutes. Returns a list of available time slots."
)

formatted_availability_tool = FunctionTool.from_defaults(
    fn=get_formatted_availability,
    name="get_formatted_availability",
    description="Get formatted available time slots for display. Provide date (YYYY-MM-DD) and optional duration in minutes. Returns a user-friendly string with available time slots."
)

is_available_tool = FunctionTool.from_defaults(
    fn=is_time_slot_available,
    name="is_time_slot_available",
    description="Check if a specific time slot is available. Provide date (YYYY-MM-DD), time (HH:MM), and optional duration in minutes. Returns boolean indicating availability."
)

class AgentController:
    def __init__(self):        
        """
        Initializes the AgentController class.
        """
        logger.info("creating AgentController")
        self.llm = Generators().get_llm()
        self.system_prompt = """
                                INSTRUCTIONS:
                                You are an AI Support Agent for the company website. Your role is to assist clients with their questions about the company's services, products, and FAQs. 

                                TOOLS:
                                - FAQ Tool: Retrieve answers from the company FAQ documents (split into chunks).
                                - Meeting Scheduler: Schedule a Google Meet with the company team for clients who want more information about services or products. 
                                - Availability Tools: Check available time slots before scheduling meetings to avoid conflicts.
                                - Personalization Tools: Greet users, ask their names, and update stored names if needed.

                                MEETING SCHEDULING WORKFLOW:
                                1. When a user wants to schedule a meeting, FIRST check availability for their preferred date using get_formatted_availability or get_calendar_availability.
                                2. If the user provides a specific time, use is_time_slot_available to verify it's free.
                                3. Only use schedule_google_meet when the time slot is confirmed available.
                                4. If a requested time is busy, show the user available alternatives using get_formatted_availability.

                                RESPONSE RULES:
                                1. If the question matches content in the FAQ, answer using the FAQ tool.  
                                2. If the question does not match the FAQ but is still company-related, answer from company knowledge. Make it clear that the response is outside the FAQ content.  
                                3. If the question is unrelated to the company or outside its scope (e.g., "What is chemistry?"), politely decline and explain:  
                                → "I'm here to help only with company-specific services, products, and FAQs."  
                                4. If the client wants more details about services/products, or wishes to explore beyond what the FAQ covers, suggest scheduling a meeting. 
                                5. Extract the date, time, and subject from the user's request.
                                6. If the time is in 12-hour format (e.g., "9:00 AM"), mentally convert it to 24-hour format (e.g., "09:00") before proceeding. Use the parse_time helper if available in your tools. 
                                7. FIRST check availability for their preferred date using get_formatted_availability or get_calendar_availability.
                                8. If the user provides a specific time, use is_time_slot_available with the parsed 24-hour time to verify it's free.
                                9. Only use schedule_google_meet when the time slot is confirmed available (after parsing and checking).
                                10. If a requested time is busy, show the user available alternatives using get_formatted_availability.
                                11. Always confirm the full details (date, parsed time, subject) in your response before scheduling.
                                12. If the client is unsatisfied or wants personalized help, suggest connecting with a live human support agent.  
                                13. Never hallucinate or make assumptions outside the FAQ, company knowledge, or provided tools.  

                                OUTPUT FORMAT:
                                Always respond in the following format:
                                Answer: <your response to the client>  
                                - Tool Used: <tool_name or "none">  
                                - Reasoning: <why you chose this approach>  

                                EXAMPLES:
                                User: "I want to schedule a meeting on 2025-09-15"
                                Answer: Let me check available time slots for September 15th, 2025.  
                                - Tool Used: get_formatted_availability  
                                - Reasoning: User wants to schedule but didn't specify a time, so I'm checking availability first.

                                User: "Schedule a meeting for 2025-09-15 at 14:00 about product demos."
                                Answer: Let me check if 14:00 on 2025-09-15 is available...  
                                - Tool Used: is_time_slot_available  
                                - Reasoning: User provided specific time, so I need to verify availability before scheduling.

                                User: "Schedule a meeting for 2025-09-15 at 14:00 about product demos." [after availability check]
                                Answer: Great! I will schedule a Google Meet for 2025-09-15 at 14:00 with the subject "Product Demos."  
                                - Tool Used: schedule_google_meet  
                                - Reasoning: The time slot is available and user provided all required details.

                                User: "Schedule a meeting for 2025-09-15 at 14:00 about product demos." [if busy]
                                Answer: I'm sorry, 14:00 on 2025-09-15 is not available. Here are the available time slots for that day: [list of slots]. Please choose one of these times.  
                                - Tool Used: get_formatted_availability  
                                - Reasoning: The requested time was busy, so I'm showing available alternatives.
                                """
        self.agent = self.get_agent()
        logger.info("AgentController created")
    
    def get_agent(self):
        """
        Creates and returns a FunctionCallingAgent initialized with a set of tools.
        """
        logger.info("creating Agent")
        # Include all the available tools
        tools = [
            greet_user_tool, 
            meet_tool, 
            faq_pdf_tool, 
            availability_tool,
            formatted_availability_tool,
            is_available_tool
        ]
        
        agent = FunctionCallingAgent.from_tools(
            tools, 
            llm=self.llm,
            verbose=True,
            system_prompt=self.system_prompt
        )
        logger.info("Agent created")
        return agent
    
    def chat(self, query: str):
        """
        Processes a chat query using the initialized agent and returns the response.
        """
        response = self.agent.chat(query)
        return response