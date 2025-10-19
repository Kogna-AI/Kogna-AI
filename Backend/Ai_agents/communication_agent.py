from crewai import Agent, Task, Crew, Process
from crewai_tools import SerpApiGoogleSearchTool
from supabase_connect import get_supabase_manager
from dotenv import load_dotenv

load_dotenv()

#connect to supabase
supabase_manager = get_supabase_manager()
supabase = supabase_manager.client

def create_communication_crew(
    synthesis_context: str,
    user_query: str,  # <--- 1. ACCEPT THE USER'S QUERY
    internal_sources: Optional[List[str]],
    google_api_key: str,
    serper_api_key: str
) -> Crew:
    """
    Creates and configures the Communications Crew.
    This crew now dynamically formats its output based on the
    user's original query.
    """

    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash", # <-- Make sure you're using the updated model name
        temperature=0.2,
        api_key=google_api_key
    )

    search_tool = SerpApiGoogleSearchTool(api_key=serper_api_key)

    communications_agent = Agent(
        role="Executive Communications Strategist",
        goal=(
            "Translate complex analytical reports into a final, user-ready answer. "
            "You must adapt your output format to perfectly match the user's original request."
        ),
        backstory=(
            "You are the final voice of Kogna AI. You receive the user's original question "
            "and the final synthesized data. Your job is to present that data in the "
            "most logical, clear, and helpful format. You are not just a report-writer; "
            "you are an answer-formatter."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[search_tool]
    )

    # --- 2. This is the new DYNAMIC task ---
    # We replace your two static tasks with this single, smart one.

    sources_text = "internal documents"
    if internal_sources:
        sources_text = ", ".join(internal_sources)
    
    dynamic_formatting_task = Task(
        description=f"""
        A user submitted a request: "{user_query}"
        
        The Kogna AI pipeline has analyzed internal and external data and
        produced the following synthesized report:
        (Internal data was sourced from: {sources_text})
        ---
        {synthesis_context}
        ---

        Your job is to format this report into a final, clean answer for the user.
        You MUST adapt your formatting to the user's original request.

        RULES:
        1.  **If the user asked for a simple list (e.g., "list of employees", "who is on the product team?"):**
            Do NOT write a big report. Simply extract the relevant list or names from
            the synthesis report and present them clearly.
        
        2.  **If the user asked for a complex analysis (e.g., "what are our risks?", "give me a report on team performance"):**
            Format the synthesis report into a professional executive summary.
            Include a brief overview, key bullet points, and a conclusion.
            At the very end,add a "Sources:" line. (e.g., "Sources: {sources_text}, Web Search")
            
        3.  **For all other requests:** Use your best judgment to present the information
            in the clearest and most direct way possible. Do not invent new information.
            Your answer should be based *only* on the synthesis report.
        """,
        expected_output="""
        The final, perfectly formatted answer for the user,
        adapted to their original query.
        If it's a complex report, it MUST end with a sources line,
        e.g., "Sources: {sources_text}, Web Search"
        """,
        agent=communications_agent
    )

    # Assemble the crew
    communication_crew = Crew(
        agents=[communications_agent],
        tasks=[dynamic_formatting_task], # <-- 3. Use the new dynamic task
        verbose=True,
        process="sequential"
    )

    return communication_crew