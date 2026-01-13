# File: Ai_agents/super_note_generator_agent.py
# SuperNoteGenerator using ChatLiteLLM

from langchain_community.chat_models import ChatLiteLLM
import os
import json
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)


class SuperNoteGenerator:
    """
    Specialized agent for generating SYNTHESIS super-notes.
    Uses ChatLiteLLM for flexible LLM provider support.
    
    Different from DocumentNoteGenerator:
    - Input: Multiple existing notes (not raw documents)
    - Output: Synthesis with insights (not just extraction)
    - Focus: Patterns, themes, implications (not just facts)
    """
    
    def __init__(self):
        """Initialize with ChatLiteLLM"""
        
        # Configure ChatLiteLLM
        # Supports: OpenAI, Anthropic, Gemini, etc.
        self.llm = ChatLiteLLM(
            model="gemini/gemini-2.0-flash-exp",  # or "gpt-4", "claude-3-sonnet", etc.
            temperature=0.4,  # Slightly higher for creative synthesis
            api_key=os.getenv("GOOGLE_API_KEY")  # or OPENAI_API_KEY, ANTHROPIC_API_KEY
        )
        
        logging.info(f"✓ SuperNoteGenerator initialized with ChatLiteLLM")
    
    def generate_super_note(
        self,
        child_notes: List[Dict],
        level: int,
        parent_context: Optional[str] = None
    ) -> Dict:
        """
        Generate a synthesis super-note from child notes.
        
        Args:
            child_notes: List of child note dicts with title, summary, key_facts
            level: Tree level (99=root, 2=theme, 1=topic)
            parent_context: Optional context from parent node
            
        Returns:
            {
                'title': str,
                'summary': str,
                'key_insights': list[str],
                'strategic_implications': list[str],
                'patterns': list[str]
            }
        """
        
        if not child_notes:
            return self._empty_note()
        
        # Route to appropriate strategy based on level
        if level == 99:
            return self._generate_root_note(child_notes)
        elif level == 2:
            return self._generate_theme_note(child_notes, parent_context)
        else:
            return self._generate_topic_note(child_notes, parent_context)
    
    def _generate_root_note(self, child_notes: List[Dict]) -> Dict:
        """
        Generate ROOT super-note (highest level overview).
        
        Goal: Executive summary of entire knowledge base
        """
        
        print(f"       Generating ROOT synthesis from {len(child_notes)} themes...")
        
        # Format child notes
        child_summaries = self._format_child_notes(child_notes)
        
        # Create synthesis prompt
        prompt = f"""You are a strategic analyst synthesizing knowledge across an entire knowledge base.

THEMES TO SYNTHESIZE:
{child_summaries}

YOUR TASK:
Create an EXECUTIVE SUMMARY that:
1. Identifies the 3-5 most important STRATEGIC THEMES across all content
2. Explains WHY these themes matter (implications, not just description)
3. Identifies patterns or connections between themes
4. Provides a compelling narrative (not a list)

STRICT RULES:
 DO NOT simply list what's in each theme
 DO NOT repeat information from child notes verbatim
 DO NOT use generic language like "this section contains..."
 DO NOT create bullet point lists in the summary

 DO synthesize across themes to find patterns
 DO provide strategic context and implications
 DO write in narrative, executive briefing style
 DO answer "so what?" and "why does this matter?"

OUTPUT FORMAT (JSON only, no markdown):
{{
    "title": "Compelling title capturing strategic narrative (under 10 words)",
    "summary": "3-4 paragraph executive summary with insights (narrative prose, no lists)",
    "key_insights": [
        "Specific insight 1 with concrete details",
        "Specific insight 2 with concrete details",
        "Specific insight 3 with concrete details"
    ],
    "strategic_implications": [
        "Specific implication 1",
        "Specific implication 2"
    ],
    "patterns": [
        "Pattern connecting multiple themes",
        "Another pattern or trend"
    ]
}}

Return ONLY valid JSON, no markdown formatting, no code blocks.
"""
        
        try:
            # Call LLM
            from langchain_core.messages import HumanMessage
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_text = response.content
            
            # Parse JSON
            result = self._parse_json_response(result_text)
            
            print(f"      ✓ ROOT synthesis complete")
            return result
        
        except Exception as e:
            logging.error(f"Root note generation failed: {e}")
            return self._fallback_note(child_notes, level=99)
    
    def _generate_theme_note(
        self, 
        child_notes: List[Dict], 
        parent_context: Optional[str]
    ) -> Dict:
        """
        Generate THEME super-note (Level 2).
        
        Goal: Synthesize a major theme with sub-topics
        """
        
        print(f"       Generating THEME synthesis from {len(child_notes)} topics...")
        
        child_summaries = self._format_child_notes(child_notes)
        parent_info = f"\n\nPARENT CONTEXT: {parent_context}\n" if parent_context else ""
        
        prompt = f"""You are a thematic analyst synthesizing related topics into a coherent theme.

{parent_info}
TOPICS TO SYNTHESIZE:
{child_summaries}

YOUR TASK:
Create a THEMATIC SYNTHESIS that:
1. Identifies the UNIFYING THEME that connects these topics
2. Explains how the topics relate to each other
3. Identifies patterns across topics
4. Provides strategic insights about this theme
5. Explains implications or "so what?"

STRICT RULES:
 DO NOT list each topic separately
 DO NOT repeat topic summaries
 DO NOT use phrases like "includes information about..."
 DO NOT create bullet points in the summary

 DO find connections between topics
 DO identify patterns and trends
 DO provide thematic insights
 DO write cohesively (narrative, not list)

OUTPUT FORMAT (JSON only, no markdown):
{{
    "title": "Theme title capturing the unifying concept (under 10 words)",
    "summary": "2-3 paragraph synthesis showing how topics connect (narrative prose)",
    "key_insights": [
        "Insight about pattern across topics",
        "Another insight with specifics",
        "Third insight connecting themes"
    ],
    "patterns": [
        "Pattern connecting topics",
        "Another pattern or trend"
    ],
    "strategic_implications": [
        "What this theme means strategically",
        "Another implication"
    ]
}}

Return ONLY valid JSON, no markdown formatting, no code blocks.
"""
        
        try:
            from langchain_core.messages import HumanMessage
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_text = response.content
            
            result = self._parse_json_response(result_text)
            
            print(f"      ✓ THEME synthesis complete")
            return result
        
        except Exception as e:
            logging.error(f"Theme note generation failed: {e}")
            return self._fallback_note(child_notes, level=2)
    
    def _generate_topic_note(
        self, 
        child_notes: List[Dict], 
        parent_context: Optional[str]
    ) -> Dict:
        """
        Generate TOPIC super-note (Level 1).
        
        Goal: Synthesize specific topic from detailed notes
        """
        
        print(f"      Generating TOPIC synthesis from {len(child_notes)} notes...")
        
        child_summaries = self._format_child_notes(child_notes)
        parent_info = f"\n\nTHEME CONTEXT: {parent_context}\n" if parent_context else ""
        
        prompt = f"""You are a focused analyst synthesizing detailed information about a specific topic.

{parent_info}
DETAILED NOTES TO SYNTHESIZE:
{child_summaries}

YOUR TASK:
Create a FOCUSED SYNTHESIS that:
1. Summarizes the specific topic clearly
2. Highlights the most important facts and figures
3. Identifies any trends or patterns in the data
4. Provides actionable insights
5. Keeps it concise but comprehensive

STRICT RULES:
 DO NOT simply concatenate child note summaries
 DO NOT use generic phrases like "this note discusses..."
 DO NOT list every detail from child notes
 DO NOT create bullet points in the summary

 DO synthesize the key information
 DO highlight what's most important
 DO identify trends or patterns
 DO provide context and insights
 DO be specific with numbers and facts

OUTPUT FORMAT (JSON only, no markdown):
{{
    "title": "Specific, descriptive topic title (under 10 words)",
    "summary": "1-2 paragraph focused synthesis (narrative prose with key data)",
    "key_insights": [
        "Specific insight with data",
        "Another insight with numbers",
        "Third insight about trends"
    ],
    "key_facts": [
        "Important fact with specifics",
        "Another key fact with data",
        "Third critical fact"
    ],
    "trends": [
        "Trend or pattern observed",
        "Another trend with data"
    ]
}}

Return ONLY valid JSON, no markdown formatting, no code blocks.
"""
        
        try:
            from langchain_core.messages import HumanMessage
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_text = response.content
            
            result = self._parse_json_response(result_text)
            
            print(f"      ✓ TOPIC synthesis complete")
            return result
        
        except Exception as e:
            logging.error(f"Topic note generation failed: {e}")
            return self._fallback_note(child_notes, level=1)
    
    def _format_child_notes(self, child_notes: List[Dict]) -> str:
        """Format child notes for the LLM"""
        formatted = []
        
        for i, note in enumerate(child_notes, 1):
            note_text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Child Note {i}]
Title: {note.get('title', 'Untitled')}

Summary:
{note.get('summary', '')}
"""
            
            # Add key facts if available
            key_facts = note.get('key_facts', [])
            if key_facts:
                note_text += "\nKey Facts:\n"
                for fact in key_facts[:5]:
                    # Remove emoji prefixes for cleaner input
                    clean_fact = fact.replace('💡 ', '').replace('📊 ', '').replace('🎯 ', '').replace('📈 ', '')
                    note_text += f"• {clean_fact}\n"
            
            formatted.append(note_text)
        
        return "\n".join(formatted)
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON from LLM response, handling markdown code blocks.
        """
        # Remove markdown code blocks if present
        cleaned = response_text.strip()
        
        # Remove ```json and ``` markers
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            # Remove first and last lines if they're code fences
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            cleaned = '\n'.join(lines).strip()
        
        # Try to parse
        try:
            result = json.loads(cleaned)
            return result
        except json.JSONDecodeError as e:
            logging.error(f"JSON parse error: {e}")
            logging.error(f"Response text: {response_text[:500]}")
            
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    return result
                except:
                    pass
            
            # Last resort: create structured output from text
            return self._extract_from_text(response_text)
    
    def _extract_from_text(self, text: str) -> Dict:
        """
        Fallback: Extract structured data from unstructured text.
        """
        lines = text.split('\n')
        
        result = {
            'title': 'Synthesis',
            'summary': '',
            'key_insights': [],
            'patterns': [],
            'strategic_implications': [],
            'key_facts': [],
            'trends': []
        }
        
        current_section = 'summary'
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Detect sections
            if 'title:' in line.lower():
                result['title'] = line.split(':', 1)[1].strip().strip('"\'')
            elif 'key insight' in line.lower() or 'insights:' in line.lower():
                current_section = 'key_insights'
            elif 'pattern' in line.lower():
                current_section = 'patterns'
            elif 'implication' in line.lower():
                current_section = 'strategic_implications'
            elif 'key fact' in line.lower():
                current_section = 'key_facts'
            elif 'trend' in line.lower():
                current_section = 'trends'
            elif 'summary:' in line.lower():
                current_section = 'summary'
                continue
            elif line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                # List item
                item = line.lstrip('-•*123456789. ').strip()
                if item and current_section in result and isinstance(result[current_section], list):
                    result[current_section].append(item)
            else:
                # Add to summary if not in a list section
                if current_section == 'summary':
                    result['summary'] += ' ' + line
        
        result['summary'] = result['summary'].strip()
        
        return result
    
    def _fallback_note(self, child_notes: List[Dict], level: int) -> Dict:
        """
        Create a basic fallback note if LLM generation fails.
        """
        titles = [note.get('title', 'Untitled') for note in child_notes]
        
        level_name = {99: 'Overview', 2: 'Theme', 1: 'Topic'}.get(level, 'Summary')
        
        return {
            'title': f'{level_name}: {len(child_notes)} Items',
            'summary': f'This section synthesizes information from {len(child_notes)} notes covering: {", ".join(titles[:3])}{"..." if len(titles) > 3 else ""}',
            'key_insights': [f'Contains information from {len(child_notes)} sources'],
            'patterns': [],
            'strategic_implications': [],
            'key_facts': titles[:5],
            'trends': []
        }
    
    def _empty_note(self) -> Dict:
        """Return empty note structure"""
        return {
            'title': 'Empty Note',
            'summary': 'No content available',
            'key_insights': [],
            'patterns': [],
            'strategic_implications': [],
            'key_facts': [],
            'trends': []
        }


# ═══════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test the generator
    generator = SuperNoteGenerator()
    
    # Sample child notes
    child_notes = [
        {
            'title': 'Q3 Revenue Performance',
            'summary': 'Q3 revenue reached $500K, representing 20% growth quarter-over-quarter. Monthly recurring revenue (MRR) increased to $45K with strong retention rates.',
            'key_facts': [
                'Revenue: $500K',
                'Growth: 20% QoQ',
                'MRR: $45K',
                'Retention: 95%'
            ]
        },
        {
            'title': 'Investor Meeting Strategy',
            'summary': 'Six investor meetings scheduled for November 13-14, 2025. Target investors include UListed, Plateau, and VacancyZero, all showing strong interest.',
            'key_facts': [
                'Meetings: 6 total',
                'Date: Nov 13-14, 2025',
                'Companies: UListed, Plateau, VacancyZero',
                'Status: High interest'
            ]
        },
        {
            'title': 'SAFE Note Structure',
            'summary': 'Dual SAFE note structure with $5M and $10M valuation caps, providing flexibility in fundraising negotiations. 20% discount included.',
            'key_facts': [
                'Cap 1: $5M',
                'Cap 2: $10M',
                'Discount: 20%',
                'Structure: Dual-cap'
            ]
        },
        {
            'title': 'Operational Cost Analysis',
            'summary': 'Monthly operational costs maintained under $1,000, demonstrating capital efficiency. Annual projected costs around $10K.',
            'key_facts': [
                'Monthly costs: <$1K',
                'Annual projection: ~$10K',
                'SaaS tools: Primary expenses',
                'Efficiency: High'
            ]
        }
    ]
    
    print("\n" + "="*70)
    print("TESTING SUPER-NOTE GENERATOR WITH CHATLITELLM")
    print("="*70)
    
    # Test Level 1 (Topic)
    print("\n\n[TEST 1] Level 1 Topic Note:")
    print("-" * 70)
    result1 = generator.generate_super_note(
        child_notes=child_notes,
        level=1,
        parent_context="Financial Strategy & Fundraising"
    )
    
    print(f"\nTitle: {result1['title']}")
    print(f"\nSummary:\n{result1['summary']}")
    print(f"\nKey Insights:")
    for insight in result1.get('key_insights', []):
        print(f"   {insight}")
    
    # Test Level 2 (Theme)
    print("\n\n[TEST 2] Level 2 Theme Note:")
    print("-" * 70)
    
    theme_notes = [
        {
            'title': 'Financial Performance & Strategy',
            'summary': result1['summary'],
            'key_facts': result1.get('key_insights', [])
        },
        {
            'title': 'Product Development Roadmap',
            'summary': 'AI-powered document analysis with focus on semantic search. Core features include hierarchical knowledge organization and intelligent retrieval.',
            'key_facts': [
                'Core tech: AI semantic search',
                'Key feature: Hierarchical knowledge',
                'Focus: Document intelligence'
            ]
        }
    ]
    
    result2 = generator.generate_super_note(
        child_notes=theme_notes,
        level=2,
        parent_context="Kogna AI Company Overview"
    )
    
    print(f"\nTitle: {result2['title']}")
    print(f"\nSummary:\n{result2['summary']}")
    print(f"\nKey Insights:")
    for insight in result2.get('key_insights', []):
        print(f"   {insight}")
    
    print(f"\nStrategic Implications:")
    for impl in result2.get('strategic_implications', []):
        print(f"   {impl}")
    
    print("\n" + "="*70)
    print(" Testing complete!")
    print("="*70 + "\n")