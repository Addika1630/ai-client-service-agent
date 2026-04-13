from llama_index.core.agent import FunctionCallingAgent
from llama_index.core.tools import FunctionTool
from src.generators import Generators
from src.tools import *
from src.utils.app_logger import GenericLogger
from src.faq_pdf_tool import query_faq_pdf
from src.jira_tool import create_jira_ticket, get_ticket_info

logger = GenericLogger().get_logger()


greet_user_tool = FunctionTool.from_defaults(fn=greet_user_and_ask_name)

jira_ticket_tool = FunctionTool.from_defaults(
    fn=create_jira_ticket,
    name="create_jira_ticket",
    description="Create a support ticket in Jira. Provide summary, description, priority (Low/Medium/High/Critical), and optionally email."
)

get_ticket_info_tool = FunctionTool.from_defaults(
    fn=get_ticket_info,
    name="get_ticket_info",
    description="Get information about an existing support ticket using the ticket ID."
)

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
                            You are an AI Support Agent for the company website. Your role is to assist clients with questions about the company's services, products, and FAQs, help create support tickets, and provide ticket status information. Always communicate clearly, politely, and professionally. Ensure answers are accurate, concise, and relevant.
                            If the client's question is ambiguous, ask clarifying questions before providing an answer. Use the tools provided when appropriate, and create a support ticket if the client's issue cannot be resolved through FAQs or requires further assistance.
                            
                            COMMUNICATION STYLE:
                            - Always be clear, polite, and professional.
                            - Responses must be concise, accurate, and relevant.
                            - Ask clarifying questions if the client's request is unclear.

                            TOOLS:
                            FAQ_Pdf_Tool: Retrieve accurate answers from company FAQ documents (split into chunks) and deliver clear, relevant responses.
                            Jira_Ticket_Tool: Create a support ticket in Jira when the client's issue cannot be resolved through FAQs or requires further assistance. The client should provide: a brief summary of the issue, detailed description, priority level (Low, Medium, High, Critical), and optionally their email address for updates. If information is missing, ask for it.
                            Get_Ticket_Info_Tool: Retrieve information about an existing support ticket using the ticket ID.
                            Greet_User_Tool: Warmly greet users, introduce what the assistant can do, and engage in normal conversation.

                            RESPONSE RULES:
                            If the question matches content in the FAQ, answer using FAQ_Pdf_Tool in a clear and concise manner.
                            If the question is related but not exactly in the FAQ and the client needs further assistance, suggest creating a support ticket.
                            If the question is unrelated to the company or outside its scope (e.g., "What is chemistry?"), politely decline and explain:
                            → "I'm here to assist only with company-specific services, products, and FAQs."
                            If the client wants more details about services/products or wishes to explore beyond what the FAQ covers, suggest creating a support ticket.
                            If the client is unsatisfied or requests personalized help, suggest creating a support ticket for dedicated assistance.
                            Never hallucinate or make assumptions outside the FAQ, company knowledge, or provided tools.
                            Provide ticket status information if the client asks about an existing ticket.
                            Always ask clarifying questions if the client query is ambiguous before providing an answer.
                            Maintain a polite, professional, and helpful tone in all interactions.

                            Before creating a ticket, always collect the client's issue summary, detailed description, and priority level. If possible, ask for their email address for updates. Do not create a ticket unless the essential details are provided. If details are missing, ask the client to provide them.

                            OUTPUT FORMAT RULES (MANDATORY):
                            All responses must follow a professional writing style suitable for client communication.

                            Formatting Standards:
                            - Always use Markdown.
                            - Each response must have three clearly labeled sections:
                            1. Answer: (main response, formatted in readable paragraphs and bullet points)
                            2. Tool Used: (state the tool name or "none")
                            3. Reasoning: (brief justification of the approach)

                            - Use line breaks between sections.
                            - Use bullet points (- ) for listing multiple services, features, or steps.
                            - Avoid inline asterisks like *this*, and instead write each point on a new line.
                            - Keep sentences concise, polite, and professional.

                            Example Format:
                            Answer:
                            Here's what I can assist you with:

                            - Answering requests about technical topics and providing information about the services and products  
                            - Creating support tickets for issues that require further assistance  
                            - Providing status updates on existing support tickets  
                            - Assisting with general inquiries and requests  
                            
                            Tool Used: faq_pdf_tool  
                            Reasoning: The response was based on company FAQ information.
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
        agent = FunctionCallingAgent.from_tools([greet_user_tool, jira_ticket_tool, get_ticket_info_tool, faq_pdf_tool], 
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