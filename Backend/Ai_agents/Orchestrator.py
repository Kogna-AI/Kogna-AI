import os
from dotenv import load_dotenv
from typing import TypedDict, Optional, List
import json
from langgraph.graph import StateGraph, END
# Assuming supabase_connect.py exists and is correct
# from supabase_connect import get_supabase_manager 
from dotenv import load_dotenv
import logging
from langchain_litellm import ChatLiteLLM
import re

load_dotenv()

#connect to supabase
# supabase_manager = get_supabase_manager()
# supabase = supabase_manager.client

# Import your existing crew creation functions
# from data_ingestion_agent import create_scribe_crew
# from data_analyst_agent import create_data_analyst_crew
from Ai_agents.internal_analyst_agent import create_internal_analyst_crew
from Ai_agents.reasearch_agent import create_research_crew
from Ai_agents.synthesize_agent import create_synthesis_crew
from Ai_agents.communication_agent import create_communication_crew

# --- 1. Define the State for the Graph ---
class WorkflowState(TypedDict):
    query_classification: Optional[str]
    user_query: str
    execution_mode: str
    chat_history: Optional[List[str]]
    internal_sources: Optional[List[str]]
    internal_analysis_report: Optional[str]
    business_research_findings: Optional[str]
    synthesis_report: Optional[str]
    final_report: Optional[str]
    error_message: Optional[str]
    human_feedback: Optional[str] # NEW: To store feedback for the loop

def node_triage_query(state: WorkflowState) -> dict:
    """Classifies the user's query as 'general_conversation' or 'data_request'."""
    print("\n--- [Node] Triaging Query ---")
    user_query = state['user_query']
    
    # --- ADDED CONTEXT ---
    chat_history = state.get("chat_history", [])
    history_str = "\n".join(chat_history)
    # Use a simple, fast LLM call for classification
    try:
        llm = ChatLiteLLM(
            model="gemini/gemini-2.0-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.0
        )
        
        prompt = f"""
        You are a conversation triage expert. You must classify the user's *latest query*
        based on the conversation history.
        Categories are: 'general_conversation' or 'data_request'.

        - 'general_conversation' is for standalone small talk, greetings, or questions about you (the AI).
        - 'data_request' is for *any* query that asks for specific data OR is a follow-up
          question related to data already discussed.

        --- CONVERSATION HISTORY ---
        {history_str}
        --- LATEST USER QUERY ---
        Human: {user_query}
        ---

        Rule: If the latest query is a pronoun (like "who are they", "what is it", "why is that")
        and the history is not empty, it is almost always a 'data_request'.
        
        Classification:
        """
        
        response = llm.invoke(prompt)
        # Clean up the response to get just the classification
        classification = response.content.strip().lower()
        
        if "general_conversation" in classification:
            print("--- [Info] Query classified as: general_conversation ---")
            return {"query_classification": "general_conversation"}
        else:
            print("--- [Info] Query classified as: data_request ---")
            return {"query_classification": "data_request"}
            
    except Exception as e:
        print(f"--- [Error] Triage failed: {e}. Defaulting to data_request. ---")
        return {"query_classification": "data_request"}

# --- 2. ADD THIS NEW "GENERAL CHAT" NODE ---
def node_answer_general_query(state: WorkflowState) -> dict:
    """Answers simple conversational queries."""
    print("\n--- [Node] Answering General Query ---")
    user_query = state['user_query']
    
    try:
        llm = ChatLiteLLM(
            model="gemini/gemini-2.0-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        
        # We can pass chat history here in the future if needed
        prompt = f"""
        You are Kogna AI, a helpful AI assistant. 
        The user said: "{user_query}"
        Respond in a brief, friendly, and conversational manner. 
        If asked your name, say you are Kogna AI.
        """
        response = llm.invoke(prompt)
        
        # This bypasses the whole crew, so we put the answer directly into 'final_report'
        return {"final_report": response.content.strip()}
        
    except Exception as e:
        print(f"--- [Error] General chat failed: {e} ---")
        return {"final_report": f"Sorry, I had an error trying to respond: {e}"}

# --- 3. ADD THIS NEW DECISION FUNCTION ---
def decide_after_triage(state: WorkflowState) -> str:
    """Decides where to route the query after classification."""
    print("\n--- [Decision] Routing based on Triage ---")
    if state.get("query_classification") == "general_conversation":
        return "answer_general_query"
    else:
        return "start_data_workflow"
# --- 2. Define the Nodes for the Graph ---

def node_internal_analyst(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Internal Analyst Crew (RAG) ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    # 1. Get both the crew and the tool instance
    internal_analyst_crew, tool_instance = create_internal_analyst_crew(gemini_api_key=google_key)
    
    inputs = {
        'user_query': state['user_query'],
        'chat_history_str': "\n".join(state.get("chat_history", [])) # Pass the history
    }
    analysis_result = internal_analyst_crew.kickoff(inputs=inputs)
    
    # 2. Get the sources from the tool's memory
    sources = tool_instance.last_chosen_files
    print(f"--- [Node] Internal Analyst used sources: {sources} ---")
    
    # 3. Return both the report and the sources to the state
    return {
        "internal_analysis_report": analysis_result.raw,
        "internal_sources": sources
    }

def node_researcher(state: WorkflowState) -> dict:
    """
    This node now ACTUALLY runs the web research crew.
    """
    print("\n--- [Node] Executing Research Crew ---")
    
    # Get API keys
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    
    if not serper_key or not google_key:
        print("--- [Node] Warning: Missing SERPAPI_API_KEY or GOOGLE_API_KEY. Skipping research. ---")
        return {"business_research_findings": "Research step skipped due to missing API keys."}

    try:
        # 1. Create the crew, passing in the user's query from the state
        research_crew = create_research_crew(
            user_query=state['user_query'], # <-- Pass the query
            google_api_key=google_key,
            serper_api_key=serper_key
        )
        
        # 2. Run the crew
        # This crew doesn't need inputs because the query is built into the task
        research_result = research_crew.kickoff()
        
        # Check if the result is not None before accessing .raw
        if research_result and hasattr(research_result, 'raw'):
            print(f"--- [Node] Research Crew finished. Findings: {research_result.raw[:100]}... ---")
            # 3. Return the findings
            return {"business_research_findings": research_result.raw}
        else:
             print("--- [Node] Research Crew returned no result. ---")
             return {"business_research_findings": "Research crew ran but produced no output."}
            
    except Exception as e:
        print(f"--- [Node] Error in Research Crew: {e} ---")
        return {"business_research_findings": f"Error during web research: {e}"}

def node_synthesizer(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Synthesizer Crew ---")
    google_key = os.getenv("GOOGLE_API_KEY")
    serper_key = os.getenv("SERPAPI_API_KEY")
    
    human_feedback = state.get("human_feedback")
    if human_feedback:
        print(f"--- [Info] Synthesizer is re-running with human feedback: '{human_feedback}' ---")
    
    synthesizer_crew = create_synthesis_crew(
        internal_analysis_report=state['internal_analysis_report'],
        internal_sources=state.get('internal_sources'), # <--- ADD THIS
        business_research_findings=state['business_research_findings'],
        google_api_key=google_key,
        serper_api_key=serper_key,
        human_feedback=human_feedback
    )
    synthesis_result = synthesizer_crew.kickoff()
    
    return {"synthesis_report": synthesis_result.raw, "human_feedback": None} # Clear feedback after use

def node_communicator(state: WorkflowState) -> dict:
    try:
        google_key = os.getenv("GOOGLE_API_KEY")
        serper_key = os.getenv("SERPAPI_API_KEY")
        
        if not serper_key or not google_key:
            raise ValueError("SERPAPI_API_KEY or GOOGLE_API_KEY not found in .env file.")

        communications_crew = create_communication_crew(
            synthesis_context=state['synthesis_report'], 
            user_query=state['user_query'],
            internal_sources=state.get('internal_sources'), # <--- ADD THIS
            google_api_key=google_key, 
            serper_api_key=serper_key
        )
        final_report_result = communications_crew.kickoff()
        return {"final_report": final_report_result.raw}
    except Exception as e:
        return {"final_report": f"Error in node_communicator: {str(e)}"}
    
def node_error_handler(state: WorkflowState) -> dict:
    print("\n--- [Node] Executing Error Handler ---")
    error_reason = state.get('internal_analysis_report', 'Unknown error in analysis')
    error_report = f"Workflow failed.\nReason: {error_reason}"
    return {"error_message": error_report}

def node_human_approval(state: WorkflowState) -> dict:
    print("\n--- [Node] Human Approval Required ---")
    synthesis_report = state.get('synthesis_report', 'No report was generated.')
    print("\nSYNTHESIS REPORT:")
    print("="*40, f"\n{synthesis_report}\n", "="*40)
    
    user_input = ""
    while user_input.lower() not in ['approve', 'reject']:
        user_input = input("Please type 'approve' to continue or 'reject' to provide feedback: ")
        
    if user_input.lower() == 'reject':
        feedback = input("Please provide feedback on what to change: ")
        return {"human_feedback": feedback}
    
    return {"human_feedback": None} # Approved, no feedback needed

# --- 3. Define the Decision Functions ---

def decide_next_step_after_analysis(state: WorkflowState) -> str:
    print("\n--- [Decision] Evaluating Internal Analysis Report ---")
    report = state.get("internal_analysis_report", "")
    
    if (
        report.startswith("Error:") 
        or report.startswith("No relevant internal documents were found")
        or "Error during router LLM call" in report
        or "Router failed" in report
    ):
        print(f"--- [Decision] Genuine error detected. Routing to error handler. ---")
        return "handle_error"
        
    print("--- [Decision] Analysis successful. Proceeding to research. ---")
    return "proceed_to_research"

def decide_if_human_approval_is_needed(state: WorkflowState) -> str:
    print("\n--- [Decision] Checking Execution Mode ---")
    if state.get("execution_mode") == "micromanage":
        return "request_approval"
    return "skip_approval"
        
def decide_after_approval(state: WorkflowState) -> str:
    print("\n--- [Decision] Evaluating Human Input ---")
    if state.get("human_feedback"):
        print("--- [Decision] Rejection with feedback received. Rerunning synthesis. ---")
        return "rerun_synthesis"
    else:
        print("--- [Decision] Approved. Proceeding to communications. ---")
        return "proceed_to_comms"

# --- 4. Build the Graph (NEW FUNCTION) ---

def get_compiled_app():
    """
    Builds and compiles the LangGraph workflow.
    """
    workflow = StateGraph(WorkflowState)

    # --- Add all your nodes ---
    workflow.add_node("triage_node", node_triage_query)                 # <--- NEW
    workflow.add_node("answer_general_query_node", node_answer_general_query)
    workflow.add_node("internal_analyst_node", node_internal_analyst)
    workflow.add_node("researcher_node", node_researcher)
    workflow.add_node("synthesizer_node", node_synthesizer)
    workflow.add_node("human_approval_node", node_human_approval)
    workflow.add_node("communicator_node", node_communicator)
    workflow.add_node("error_handler_node", node_error_handler)

    # --- Set the entry point ---
    workflow.set_entry_point("triage_node")

    # --- Add all your edges ---
    workflow.add_conditional_edges(
        "triage_node",
        decide_after_triage,
        {
            "answer_general_query": "answer_general_query_node", # If small talk, answer and finish
            "start_data_workflow": "internal_analyst_node"      # If data, start the main crew
        }
    )
    workflow.add_edge("answer_general_query_node", END) # <--- NEW
    workflow.add_conditional_edges(
        "internal_analyst_node",
        decide_next_step_after_analysis, 
        {"handle_error": "error_handler_node", "proceed_to_research": "researcher_node"}
    )
    workflow.add_edge("researcher_node", "synthesizer_node")
    workflow.add_conditional_edges(
        "synthesizer_node", 
        decide_if_human_approval_is_needed, 
        {"request_approval": "human_approval_node", "skip_approval": "communicator_node"}
    )
    workflow.add_conditional_edges(
        "human_approval_node", 
        decide_after_approval, 
        {"proceed_to_comms": "communicator_node", "rerun_synthesis": "synthesizer_node"}
    )
    workflow.add_edge("communicator_node", END)
    workflow.add_edge("error_handler_node", END)

    # --- Compile the app ---
    return workflow.compile()


# --- Main execution block for Continuous Chat ---
if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='kogna_ai.log', # This file will store all the process logs
        filemode='w' # 'w' overwrites the log each time, 'a' appends
    )
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    print("--- Welcome to the Kogna AI Orchestrator (Chat Mode) ---")
    print("Type 'quit' or 'exit' to end the conversation.")

    # --- Compile the graph ONCE at the start ---
    load_dotenv() # Ensure env vars are loaded before compiling
    try:
        # This call will now succeed
        app = get_compiled_app()
        print("--- LangGraph App Compiled ---")
    except Exception as e:
        print(f"FATAL ERROR: Could not compile LangGraph app: {e}")
        # exit() # Removed exit() so you can debug if needed

    # --- Initialize chat history ---
    chat_history = []

    # --- Start the conversation loop ---
    while True:
        # 1. Get user input
        query = input("\nYou: ")
        if query.lower() in ["quit", "exit"]:
            print("\nKogna AI: Goodbye! 👋")
            break
        if not query.strip(): # Check for empty input
            continue

        # 2. Set up initial state for this turn
        initial_state = {
            "user_query": query,
            "chat_history": chat_history.copy(), # Pass current history
            "execution_mode": "autonomous", # Keep it simple for chat
            # Initialize all state keys to None or default values
            "query_classification": None,
            "internal_analysis_report": None,
            "internal_sources": None,
            "business_research_findings": None,
            "synthesis_report": None,
            "final_report": None,
            "error_message": None,
            "human_feedback": None,
        }

        print("\nKogna AI is thinking... 🤔")
        final_report = None
        stream_error = None
        full_stream_output = [] # Optional: Capture intermediate steps

        # 3. Run the graph stream
        try:
            # Loop through the stream output from the graph
            for s in app.stream(initial_state, {"recursion_limit": 25}):
                full_stream_output.append(s)

                # --- START: MODIFIED LOGIC ---
                # Check for an answer from EITHER the general chat OR the communicator
                
                final_answer_node = None
                if "answer_general_query_node" in s:
                    final_answer_node = s.get("answer_general_query_node")
                elif "communicator_node" in s:
                    final_answer_node = s.get("communicator_node")

                # If we found an answer node and it's not empty
                if final_answer_node is not None:
                    report = final_answer_node.get("final_report")
                    if report:
                        final_report = report
                
                # --- END: MODIFIED LOGIC ---

                # Check if the error handler node ran
                elif "error_handler_node" in s:
                     node_output = s["error_handler_node"]
                     if node_output is not None:
                         error_msg = node_output.get("error_message")
                         if error_msg:
                             final_report = f"Sorry, I encountered an error: {error_msg}"
                             stream_error = True

        except Exception as e:
            print(f"\n--- WORKFLOW EXECUTION ERROR ---")
            print(f"An error occurred while running the graph stream: {e}")
            final_report = f"Sorry, a critical error occurred during processing: {e}"
            stream_error = True

        # 4. Print the final AI response
        if final_report:
            print(f"\nKogna AI: {final_report}")
            # 5. Update chat history only on successful completion or handled error
            chat_history.append(f"Human: {query}")
            chat_history.append(f"AI: {final_report}")
        elif not stream_error:
            print("\nKogna AI: I finished processing but couldn't generate a final report. 🤔")
            print("--- DEBUG: No final report found in stream output. Last few outputs: ---")
            print(full_stream_output[-3:])
            chat_history.append(f"Human: {query}")
            chat_history.append(f"AI: [Processing completed without a final report]")
        
        # Optional: Limit chat history size
        MAX_HISTORY_TURNS = 5 # Keep last 5 pairs (10 messages total)
        if len(chat_history) > MAX_HISTORY_TURNS * 2:
             print("--- Pruning chat history ---")
             chat_history = chat_history[-(MAX_HISTORY_TURNS * 2):]