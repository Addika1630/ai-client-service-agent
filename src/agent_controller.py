from llama_index.core.agent import FunctionCallingAgent
from llama_index.core.tools import FunctionTool
from src.generators import Generators
from src.tools import *
from src.utils.app_logger import GenericLogger
from src.faq_pdf_tool import query_faq_pdf

logger = GenericLogger().get_logger()


greet_user_tool = FunctionTool.from_defaults(fn=greet_user_and_ask_name)

meet_tool = FunctionTool.from_defaults(
    fn=schedule_google_meet,
    name="schedule_google_meet",
    description="Schedule a Google Meet meeting. Provide date (YYYY-MM-DD), time (HH:MM), subject, and optionally duration."
)

available_slots_tool = FunctionTool.from_defaults(fn=available_slots)
# Create the FAQ tool from PDF documents
faq_pdf_tool = FunctionTool.from_defaults(
    fn=query_faq_pdf,
    name="faq_pdf_tool",
    description="Answer company FAQs from PDF files."
)

class AgentController:
    def __init__(self):        
        """
        Initializes the AgentController class.

        This method creates an instance of the AgentController class with the LLaMA model and the system prompt.

        The system prompt is a string that is provided to the LLaMA model to generate responses.
        """

        logger.info("creating AgentController")
        self.llm = Generators().get_llm()
        self.system_prompt = """
                            INSTRUCTIONS:
                            You are an AI Support Agent for the company website. Your role is to assist clients with questions about the company’s services, products, and FAQs, help schedule meetings, provide available meeting slots, and support other requests. Always communicate clearly, politely, and professionally. Ensure answers are accurate, concise, and relevant.
                            If the client’s question is ambiguous, ask clarifying questions before providing an answer. Use the tools provided when appropriate, and escalate to schedule a meeting if the client requests further information or the question cannot be handled.
                            
                            COMMUNICATION STYLE:
                            - Always be clear, polite, and professional.
                            - Responses must be concise, accurate, and relevant.
                            - Ask clarifying questions if the client’s request is unclear.

                            TOOLS:
                            FAQ_Pdf_Tool: Retrieve accurate answers from company FAQ documents (split into chunks) and deliver clear, relevant responses.
                            Meet_Tool: Schedule a Google Meet with the correct team (Sales or Technical). The client MUST specify the team and provide: date (YYYY-MM-DD UTC), time (HH:MM UTC), email address (to send the invite), and a title/subject. If team is not specified or unclear, ask: "Which team would you like to meet: Sales or Technical?" If any detail is missing or in the wrong format, politely ask the client to provide it.
                            Greet_User_Tool: Warmly greet users, introduce what the assistant can do, and engage in normal conversation.
                            Available_Slots_Tool: Provide a list of available meeting slots for a specified team (Sales or Technical). If the team is not specified, ask the client to choose.

                            RESPONSE RULES:
                            If the question matches content in the FAQ, answer using FAQ_Pdf_Tool in a clear and concise manner.
                            If the question is related but not exactly in the FAQ and the client wants more information, suggest scheduling a meeting to learn more.
                            If the question is unrelated to the company or outside its scope (e.g., “What is chemistry?”), politely decline and explain:
                            → “I’m here to assist only with company-specific services, products, and FAQs.
                            If the client wants more details about services/products or wishes to explore beyond what the FAQ covers, suggest scheduling a meeting.
                            If the client is unsatisfied or requests personalized help, suggest connecting with a live support agent or scheduling a meeting.
                            Never hallucinate or make assumptions outside the FAQ, company knowledge, or provided tools.
                            Return available meeting slots if the client asks for them.
                            If the client tries to schedule a meeting in the past, inform them the time is invalid and suggest available slots.
                            If the client tries to schedule a meeting during restricted nighttime hours, inform them the time is not allowed and suggest available slots.
                            If the client tries to schedule a meeting in a time that is already booked, inform them the slot is unavailable and suggest available slots.
                            If the client provides a meeting time in a different time zone or in an unclear format, notify them that all times must be in UTC and ask for the correct time.
                            Always ask clarifying questions if the client query is ambiguous before providing an answer.
                            Maintain a polite, professional, and helpful tone in all interactions.
                            Before confirming a meeting, always collect the client's email, date (YYYY-MM-DD UTC), time (HH:MM UTC), and meeting subject. Do not schedule a meeting unless all these details are provided and valid. If any detail is missing or invalid, ask the client to provide it. Scheduling without these details is strictly prohibited.

                            OUTPUT FORMAT RULES (MANDATORY):
                            All responses must follow a professional writing style suitable for client communication.

                            Formatting Standards:
                            - Always use Markdown.
                            - Each response must have three clearly labeled sections:
                            1. **Answer:** (main response, formatted in readable paragraphs and bullet points)
                            2. **Tool Used:** (state the tool name or "none")
                            3. **Reasoning:** (brief justification of the approach)

                            - Use line breaks between sections.
                            - Use bullet points (`- `) for listing multiple services, features, or steps.
                            - Avoid inline asterisks like *this*, and instead write each point on a new line.
                            - Keep sentences concise, polite, and professional.

                            Example Format:
                            **Answer:**
                            Here’s what I can assist you with:

                            - Answering company FAQs and providing information about services and products  
                            - Scheduling Google Meet meetings with the company team  
                            - Providing available meeting slots for clients to choose from  
                            - Assisting with general inquiries and requests  
                            - Escalating complex issues to live support agents when necessary  

                            **Tool Used:** faq_pdf_tool  
                            **Reasoning:** The response was based on company FAQ information.
                            """
        self.agent = self.get_agent()
        logger.info("AgentController created")
    def get_agent(self):
        
        """
        Creates and returns a FunctionCallingAgent initialized with a set of tools and the specified language model.

        The agent is configured to use a variety of mathematical and utility tools, 
        and is provided with a system prompt for operation. It logs the creation process.

        :return: An initialized FunctionCallingAgent instance.
        """
        logger.info("creating Agent")
        agent = FunctionCallingAgent.from_tools([greet_user_tool, meet_tool, faq_pdf_tool, available_slots_tool], 
                                        llm=self.llm,verbose=True,
                                        system_prompt=self.system_prompt)
        logger.info("Agent created")
        return agent
    
    def chat(self, query: str):
        """
        Processes a chat query using the initialized agent and returns the response.

        This method sends a user query to the agent, which processes it using the available tools 
        and language model, and returns the generated response. 

        Args:
            query (str): The query string to be processed by the agent.
        
        Returns:
            The agent's response to the provided query.
        """
        response = self.agent.chat(query)
        return response