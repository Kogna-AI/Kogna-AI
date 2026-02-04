"""
Document Note Generator Agent for HCR (Hierarchical Contextual Retrieval)
Generates intelligent summaries from uploaded documents
"""

from crewai import Agent, Task, Crew
from Ai_agents.llm_factory import get_llm_for_agent
import json
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class DocumentNoteGenerator:
    """
    AI agent that generates structured notes from documents.
    This is the core of HCR - creating intelligent summaries instead of just chunks.
    """
    
    def __init__(self, user_id: Optional[str] = None):
        # Initialize Gemini model using ChatLiteLLM (same as orchestrator)
        self.llm = get_llm_for_agent(agent_name="some agent", user_id=user_id,temperature_override=0.3)
        
        # Create the note generator agent
        self.note_generator = Agent(
            role="Document Intelligence Analyst",
            goal="Extract key information and generate structured notes from documents",
            backstory="""You are an expert at analyzing documents and creating 
            comprehensive, structured summaries. You identify key facts, entities, 
            action items, and relationships. Your notes are the foundation for 
            the HCR (Hierarchical Contextual Retrieval) system that makes AI intelligent.
            
            You focus on:
            - Extracting concrete facts with numbers and dates
            - Identifying entities (people, companies, dates, metrics)
            - Finding actionable items
            - Creating coherent summaries that capture the document's essence
            
            Your summaries are NOT just shortened versions - they are intelligent 
            distillations that highlight what matters.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def generate_note(self, document_text: str, file_path: str) -> dict:
        """
        Generate a structured note from document text.
        
        Args:
            document_text: Full text from all chunks of the document
            file_path: Path to the document (e.g., "uploads/user123/Q3_Report.pdf")
            
        Returns:
            dict: Structured note with title, summary, facts, entities, etc.
        """
        
        # Extract filename from path for better title generation
        filename = file_path.split('/')[-1]
        
        # Create the task
        task = Task(
            description=f"""
            Analyze this document and create a comprehensive structured note.
            
            Document Filename: {filename}
            Document Text (first 8000 chars):
            {document_text[:8000]}
            
            YOUR TASK:
            Generate a JSON object with these exact fields:
            
            {{
              "title": "Clear, descriptive title (improve on filename if needed)",
              "summary": "2-3 paragraph comprehensive summary (150-300 words). Make it coherent and complete.",
              "key_facts": [
                "Array of 5-10 most important facts",
                "Be specific - include numbers, dates, percentages",
                "Each fact should be standalone and precise"
              ],
              "action_items": [
                "Actionable items mentioned or implied",
                "Things that need to be done",
                "Can be empty array if none found"
              ],
              "entities": {{
                "people": ["Names of people mentioned"],
                "companies": ["Company/organization names"],
                "dates": ["Important dates in YYYY-MM-DD or 'Q3 2024' format"],
                "metrics": ["Key metrics/KPIs like 'revenue', 'growth rate', 'margin'"],
                "topics": ["Main topics/themes like 'financials', 'strategy', 'product']
              }}
            }}
            
            CRITICAL RULES:
            1. Be FACTUAL and PRECISE - only include what's in the document
            2. Include SPECIFIC NUMBERS and DATES wherever possible
            3. Extract ENTITIES exactly as they appear
            4. Make the SUMMARY coherent - it should read well on its own
            5. KEY FACTS should be standalone sentences (readable without context)
            6. If information is missing, use empty array [] or empty object {{}}
            7. Return ONLY valid JSON - no markdown, no code blocks, no explanation
            
            QUALITY EXAMPLES:
            
            Good key fact: "Revenue reached $2.5M in Q3 2024, up 15% from Q2"
            Bad key fact: "Revenue increased" (too vague)
            
            Good summary: "The Q3 2024 financial report shows strong revenue growth..."
            Bad summary: "This document talks about finances..." (too generic)
            
            Return your response as pure JSON.
            """,
            agent=self.note_generator,
            expected_output="Valid JSON object with title, summary, key_facts, action_items, and entities"
        )
        
        # Execute the task
        crew = Crew(
            agents=[self.note_generator],
            tasks=[task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Parse the JSON result
        note_data = self._parse_json_result(str(result))
        
        # Validate the note has required fields
        self._validate_note(note_data)
        
        return note_data
    
    def _parse_json_result(self, result_text: str) -> dict:
        """Parse JSON from the AI result, handling markdown code blocks if present."""
        try:
            # Try direct JSON parse first
            return json.loads(result_text)
        except json.JSONDecodeError:
            # Try to extract from markdown code block
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                json_str = result_text[json_start:json_end].strip()
                return json.loads(json_str)
            elif "```" in result_text:
                # Generic code block
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                json_str = result_text[json_start:json_end].strip()
                return json.loads(json_str)
            else:
                raise ValueError(f"Could not parse JSON from result: {result_text[:200]}")
    
    def _validate_note(self, note_data: dict):
        """Ensure the note has all required fields."""
        required_fields = ['title', 'summary', 'key_facts', 'action_items', 'entities']
        
        for field in required_fields:
            if field not in note_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Ensure entities is a dict
        if not isinstance(note_data['entities'], dict):
            raise ValueError("entities must be a dictionary")
        
        # Ensure arrays are arrays
        if not isinstance(note_data['key_facts'], list):
            raise ValueError("key_facts must be an array")
        if not isinstance(note_data['action_items'], list):
            raise ValueError("action_items must be an array")


# ============================================
# USAGE EXAMPLE / TEST
# ============================================

if __name__ == "__main__":
    """
    Test the note generator with sample document text
    """
    
    print("🧪 Testing Document Note Generator...")
    print("=" * 60)
    
    # Sample document text
    sample_document = """
    Q3 2024 Financial Performance Report
    Executive Summary
    
    Kogna achieved strong revenue growth in Q3 2024, with total revenue 
    reaching $2.5 million, representing a 15% increase from Q2 2024 ($2.17M).
    
    Key Financial Metrics:
    - Total Revenue: $2.5M (+15% QoQ)
    - Operating Expenses: $1.8M (+12% QoQ)
    - Net Profit: $700K
    - Profit Margin: 28% (down from 30% in Q2)
    - Monthly Recurring Revenue (MRR): $850K
    - Customer Acquisition Cost (CAC): $1,200 (improved from $1,500)
    
    Revenue Breakdown:
    The revenue increase was driven primarily by:
    1. New enterprise customers (contributed $400K)
    2. Expansion revenue from existing customers (+$230K)
    3. New product line launch (+$100K)
    
    Expense Analysis:
    Operating expenses increased to $1.8M, up 12% from Q2. Main drivers:
    - Engineering team expansion: +$150K
    - Marketing campaigns: +$80K
    - Infrastructure costs: +$60K
    
    Customer Metrics:
    - Total Customers: 450 (up from 380 in Q2)
    - Churn Rate: 2.3% (stable)
    - Net Revenue Retention: 115%
    
    Action Items for Q4:
    1. Optimize marketing spend to reduce CAC further (target: $1,000)
    2. Review infrastructure costs for potential savings
    3. Launch premium tier to improve margins
    4. Expand sales team by 3 people
    
    Notable Achievements:
    - Closed 2 enterprise deals worth $300K ARR each
    - Product feature adoption rate: 78%
    - Customer satisfaction score: 4.6/5
    
    Prepared by: Sarah Chen, CFO
    Date: October 15, 2024
    """
    
    # Initialize generator
    generator = DocumentNoteGenerator()
    
    # Generate note
    try:
        note = generator.generate_note(
            document_text=sample_document,
            file_path="uploads/user123/Q3_2024_Financial_Report.pdf"
        )
        
        print("\n NOTE GENERATED SUCCESSFULLY!")
        print("=" * 60)
        print("\n TITLE:")
        print(note['title'])
        
        print("\n SUMMARY:")
        print(note['summary'])
        
        print("\n KEY FACTS:")
        for i, fact in enumerate(note['key_facts'], 1):
            print(f"  {i}. {fact}")
        
        print("\n  ACTION ITEMS:")
        for i, item in enumerate(note['action_items'], 1):
            print(f"  {i}. {item}")
        
        print("\n  ENTITIES:")
        print(json.dumps(note['entities'], indent=2))
        
        print("\n" + "=" * 60)
        print(" Test completed successfully!")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()