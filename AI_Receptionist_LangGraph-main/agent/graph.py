from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode
import datetime
import time  # FIX BUG-23: for retry backoff
from .tools import (
    check_availability_ml, book_appointment, cancel_appointment,
    get_next_available_appointment, generate_qr_code, register_visitor
)
from database.models import Doctor, DiseaseSpecialty
from database.connection import get_session
from langchain_core.messages import HumanMessage

# Import ChatGroq instead of OpenAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# FIX BUG-09: Guard against missing GROQ_API_KEY to prevent silent None assignment or TypeError
_groq_api_key = os.getenv("GROQ_API_KEY")
if not _groq_api_key:
    raise EnvironmentError(
        "GROQ_API_KEY is not set. Please add it to your .env file. "
        "The application cannot start without a valid Groq API key."
    )
os.environ["GROQ_API_KEY"] = _groq_api_key

# Initialize the Groq model with the necessary parameters
llm = ChatGroq(model="llama3-70b-8192", temperature=0.5)


# Function to process and respond to user messages
def run_agent(history):
    """
    Runs the agent with the provided message history.
    Args:
        history: List of LangChain message objects (HumanMessage, AIMessage, etc.)
    Returns:
        The updated history or the final response content.
    """
    state = {
        "messages": history,
    }
    
    # Invoke the graph
    # configured to handle the conversation
    result = caller_app.invoke(state)
    
    # Return the last message (response)
    return result["messages"][-1]


# Edge function for determining conversation continuation
def should_continue_caller(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"

# Node function to call the Groq model
def call_caller_model(state: MessagesState):
    # FIX BUG-10: Do NOT mutate state with state["current_time"] — MessagesState
    # only accepts the "messages" key. Pass current_time via the prompt input dict.
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # FIX BUG-23: Retry with exponential backoff for transient API errors
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = caller_model.invoke({
                "messages": state["messages"],
                "current_time": current_time
            })
            return {"messages": [response]}
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait)
            else:
                raise  # Re-raise after all retries exhausted

# List of tools for managing appointments
caller_tools = [
    book_appointment, 
    get_next_available_appointment, 
    cancel_appointment,
    check_availability_ml,
    generate_qr_code,
    register_visitor
]
tool_node = ToolNode(caller_tools)

# Define prompt template for the assistant
caller_pa_prompt = """You are a smart AI Receptionist. 
Capabilities:
1. Booking/Cancelling Appointments: Always check strict time availability. Use 'check_availability_ml' to see if a time slot is optimal.
2. Visitor Check-in: You can register visitors. Ask for their Name, Purpose, and Company.
3. QR Codes: You can generate QR codes for confirmed appointments.

Be polite, professional, and helpful.
Current time: {current_time}
"""

# Define the chat prompt template
caller_chat_template = ChatPromptTemplate.from_messages([
    ("system", caller_pa_prompt),
    ("placeholder", "{messages}"),
])

# Bind the tools to the Groq model and set up the model pipeline
caller_model = caller_chat_template | llm.bind_tools(caller_tools)

# Initialize the graph and workflow
caller_workflow = StateGraph(MessagesState)

# Add nodes for the workflow
caller_workflow.add_node("agent", call_caller_model)
caller_workflow.add_node("action", tool_node)

# Define conditional edges for the workflow
caller_workflow.add_conditional_edges(
    "agent",
    should_continue_caller,
    {
        "continue": "action",
        "end": END,
    },
)
caller_workflow.add_edge("action", "agent")

# Set the entry point and compile the workflow
caller_workflow.set_entry_point("agent")
caller_app = caller_workflow.compile()
