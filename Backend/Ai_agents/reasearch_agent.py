# Backend/Ai_agents/research_agent.py
from crewai import Agent, Task, Crew
from crewai_tools import SerpApiGoogleSearchTool
from langchain_litellm import ChatLiteLLM
from dotenv import load_dotenv
import logging
import re
import time
from functools import wraps

# --- Import prompts ---
from .prompt import (
    RESEARCHER_ROLE,
    RESEARCHER_GOAL,
    RESEARCHER_BACKSTORY,
    RESEARCHER_TASK_DESCRIPTION,
    RESEARCHER_EXPECTED_OUTPUT
)

load_dotenv()

# =================================================================
# HELPER FUNCTIONS
# =================================================================

def extract_key_entities(query: str) -> list[str]:
    """
    Extract potential company/product names from the query.
    Simple heuristic: capitalized words and quoted terms.
    """
    # Find quoted terms
    quoted = re.findall(r'"([^"]+)"', query)
    
    # Find capitalized words (potential proper nouns)
    words = query.split()
    capitalized = [w for w in words if w and w[0].isupper() and len(w) > 2]
    
    entities = list(set(quoted + capitalized))
    logging.info(f"[Research] Extracted entities: {entities}")
    return entities

def validate_research_results(query: str, results: str) -> tuple[bool, str]:
    """
    Validate that research results are actually about what was asked.
    Returns: (is_valid, error_message)
    """
    # Extract entities from original query
    query_entities = extract_key_entities(query)
    
    if not query_entities:
        # Can't validate without clear entities
        return True, ""
    
    # Convert to lowercase for case-insensitive comparison
    results_lower = results.lower()
    
    # Check if ANY of the key entities appear in the results
    entities_found = [e for e in query_entities if e.lower() in results_lower]
    
    if not entities_found:
        # Look for common wrong matches
        wrong_matches = []
        
        # Common confusions
        confusion_pairs = [
            ("kogna", "kogan"),
            ("tableau", "table"),
            ("qlik", "click"),
        ]
        
        for correct, wrong in confusion_pairs:
            if correct.lower() in [e.lower() for e in query_entities]:
                if wrong in results_lower and correct.lower() not in results_lower:
                    wrong_matches.append(f"Found '{wrong}' instead of '{correct}'")
        
        if wrong_matches:
            error_msg = f"Search returned wrong entity: {', '.join(wrong_matches)}"
            logging.warning(f"[Research] Validation failed: {error_msg}")
            return False, error_msg
        
        # Generic entity mismatch
        error_msg = f"Results don't mention any key entities: {query_entities}"
        logging.warning(f"[Research] Validation failed: {error_msg}")
        return False, error_msg
    
    # Check for "online retailer" when asking about AI/software
    if any(term in query.lower() for term in ["ai", "software", "platform", "saas"]):
        if "online retailer" in results_lower or "e-commerce" in results_lower:
            error_msg = "Found retail company instead of AI/software company"
            logging.warning(f"[Research] Validation failed: {error_msg}")
            return False, error_msg
    
    logging.info(f"[Research] Validation passed. Found entities: {entities_found}")
    return True, ""

# =================================================================
# CREW CREATION
# =================================================================

def create_research_crew(
    user_query: str,
    google_api_key: str,
    serper_api_key: str,
) -> Crew:
    """
    Creates and configures the Business Research Crew with improved prompts
    and result validation.
    """
    logging.info(f"[Research] Creating crew for query: '{user_query}'")
    
    # --- Agent Configuration ---
    llm = ChatLiteLLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.4,  # Lower temperature for more precise research
        api_key=google_api_key
    )
    
    search_tool = SerpApiGoogleSearchTool(api_key=serper_api_key)
    
    research_agent = Agent(
        role=RESEARCHER_ROLE,
        goal=RESEARCHER_GOAL.format(user_query=user_query),
        backstory=RESEARCHER_BACKSTORY,
        verbose=True,  # Set to True to see search queries
        allow_delegation=False,
        llm=llm,
        tools=[search_tool]
    )
    
    # --- Task Definition ---
    web_research_task = Task(
        description=RESEARCHER_TASK_DESCRIPTION.format(user_query=user_query),
        expected_output=RESEARCHER_EXPECTED_OUTPUT.format(user_query=user_query),
        agent=research_agent
    )
    
    # Create and return the Crew
    research_crew = Crew(
        agents=[research_agent],
        tasks=[web_research_task],
        verbose=True,  # Set to True for debugging
        process="sequential"
    )
    
    return research_crew

# =================================================================
# MAIN FUNCTION WITH RATE LIMIT + VALIDATION
# =================================================================

def run_research_with_validation(
    user_query: str,
    google_api_key: str,
    serper_api_key: str,
    max_validation_retries: int = 2
) -> str:
    """
    Wrapper function that runs research and validates results.
    Includes rate limit retry with exponential backoff.
    """
    
    # Outer loop: Rate limit retries
    max_rate_limit_retries = 3
    base_delay = 3
    
    for rate_attempt in range(max_rate_limit_retries):
        
        # Inner loop: Validation retries
        for validation_attempt in range(max_validation_retries):
            logging.info(
                f"[Research] Rate attempt {rate_attempt + 1}/{max_rate_limit_retries}, "
                f"Validation attempt {validation_attempt + 1}/{max_validation_retries}"
            )
            
            # Create and run crew
            crew = create_research_crew(user_query, google_api_key, serper_api_key)
            
            try:
                result = crew.kickoff()
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                is_rate_limit = (
                    "429" in error_str or
                    "rate limit" in error_str or
                    "resource exhausted" in error_str or
                    "quota" in error_str
                )
                
                if is_rate_limit:
                    if rate_attempt < max_rate_limit_retries - 1:
                        delay = base_delay * (2 ** rate_attempt)  # Exponential backoff
                        logging.warning(
                            f"[Research] Rate limited. Retrying in {delay}s... "
                            f"(attempt {rate_attempt + 1}/{max_rate_limit_retries})"
                        )
                        time.sleep(delay)
                        break  # Break inner loop, continue outer loop
                    else:
                        # Out of rate limit retries
                        logging.error("[Research] Rate limit retries exhausted")
                        return (
                            "Research temporarily unavailable due to API rate limits. "
                            "Please try again in a few minutes."
                        )
                else:
                    # Not a rate limit error
                    logging.error(f"[Research] Crew execution failed: {e}")
                    return (
                        f"Research failed due to error: {str(e)[:500]}\n\n"
                        f"Original query: {user_query}"
                    )
            
            # If we got here, crew executed successfully
            # Now validate results
            is_valid, error_msg = validate_research_results(user_query, result.raw)
            
            if is_valid:
                logging.info("[Research] ✅ Validation passed, returning results")
                return result.raw
            
            # Validation failed
            logging.warning(
                f"[Research] ❌ Validation failed (attempt {validation_attempt + 1}): {error_msg}"
            )
            
            if validation_attempt < max_validation_retries - 1:
                # Add explicit disambiguation to query for retry
                entities = extract_key_entities(user_query)
                if entities:
                    user_query = f'"{entities[0]}" {user_query}'
                    logging.info(f"[Research] Retrying with disambiguated query: {user_query}")
                    time.sleep(2)  # Brief pause before validation retry
            else:
                # All validation retries exhausted
                logging.error("[Research] All validation attempts failed")
                return (
                    f"Research validation failed: {error_msg}\n\n"
                    f"The search returned irrelevant results. This could mean:\n"
                    f"1. The entity has minimal online presence\n"
                    f"2. The entity name is ambiguous or misspelled\n"
                    f"3. The search engine is confusing it with a similar-named entity\n\n"
                    f"Original query: {user_query}"
                )
    
    # Should never reach here
    return "Research failed after maximum retries."