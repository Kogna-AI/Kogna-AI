# fact_extraction.py
"""
Kogna Fact Extraction System
============================

Automatically extracts business facts, risks, metrics, and context
from user conversations using LLM.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import json
import re


# ============================================================
# EXTRACTION SCHEMAS
# ============================================================

class ExtractedFact(BaseModel):
    """A piece of business knowledge extracted from conversation"""
    fact_type: str  # company_info, metric_value, temporal_event, relationship, business_rule
    subject: str
    predicate: str
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str
    temporal_context: Optional[str] = None


class ExtractedRisk(BaseModel):
    """A risk extracted from conversation"""
    title: str
    description: str
    category: str  # financial, operational, compliance, strategic, market
    severity: str  # critical, high, medium, low, unknown
    cause: Optional[str] = None
    impact: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str


class ExtractedMetric(BaseModel):
    """A metric or KPI extracted from conversation"""
    metric_name: str
    metric_type: str  # value, target, definition, comparison
    value: Optional[Any] = None
    unit: Optional[str] = None
    time_period: Optional[str] = None
    comparison: Optional[str] = None
    definition: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str


class ExtractedCompanyInfo(BaseModel):
    """Company information extracted from conversation"""
    info_type: str  # name, industry, location, size, product, fiscal_year, structure
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str


class ExtractedPreference(BaseModel):
    """User preference extracted from conversation"""
    preference_type: str  # visualization, detail_level, tone, frequency, format
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str


class ExtractionResult(BaseModel):
    """Complete result of fact extraction from a conversation"""
    facts: List[ExtractedFact] = []
    risks: List[ExtractedRisk] = []
    metrics: List[ExtractedMetric] = []
    company_info: List[ExtractedCompanyInfo] = []
    preferences: List[ExtractedPreference] = []
    has_extractable_content: bool = False


# ============================================================
# EXTRACTION PROMPTS
# ============================================================

EXTRACTION_SYSTEM_PROMPT = """You are a business intelligence fact extractor. Your job is to extract structured business information from user messages in conversations with an AI assistant.

IMPORTANT RULES:
1. Extract ONLY facts that are explicitly stated or strongly implied
2. Do not infer or assume information not present
3. Assign appropriate confidence scores (0.0-1.0) based on how explicit the information is
4. Include the source_text - the exact phrase that contains the information

CATEGORIES TO EXTRACT:

1. COMPANY_INFO: Information about the user's company
   - Types: name, industry, location, size, product, fiscal_year, structure, market
   - Example: "We're a B2B SaaS company" → {info_type: "industry", value: "B2B SaaS"}

2. METRICS: Business metrics and KPIs
   - Types: value (actual number), target (goal), definition (how they define it), comparison (change)
   - Include time_period if mentioned (Q3, last month, 2024, etc.)
   - Example: "Revenue was $5M in Q3" → {metric_name: "revenue", metric_type: "value", value: 5000000, unit: "USD", time_period: "Q3"}

3. RISKS: Business risks and concerns
   - Categories: financial, operational, compliance, strategic, market
   - Severity: critical (existential threat), high (major impact), medium (moderate impact), low (minor), unknown
   - Look for: "biggest risk", "worried about", "concern", "threat", "problem", "issue"
   - Example: "Tariffs are killing our margins" → {title: "Tariff impact on margins", severity: "high", category: "financial"}

4. TEMPORAL_EVENTS: Things that happened at specific times
   - Example: "We launched in APAC in 2022" → {subject: "APAC operations", predicate: "launched_in", value: "2022"}

5. RELATIONSHIPS: Connections between business entities
   - Example: "Product X drives 60% of revenue" → {subject: "Product X", predicate: "contributes", value: "60% of revenue"}

6. PREFERENCES: User's analytical preferences (how they want information presented)
   - Types: visualization (charts/tables), detail_level (detailed/summary), tone, frequency, format
   - Example: "I prefer seeing weekly trends" → {preference_type: "frequency", value: "weekly"}

OUTPUT FORMAT: Valid JSON only. If nothing to extract, return empty arrays with has_extractable_content: false."""


EXTRACTION_USER_PROMPT = """Extract business facts from this conversation turn:

USER MESSAGE:
{user_message}

ASSISTANT RESPONSE (for context only, extract from USER message):
{assistant_response}

Return a JSON object with this exact structure:
{{
    "facts": [
        {{
            "fact_type": "company_info|metric_value|temporal_event|relationship|business_rule",
            "subject": "entity this is about",
            "predicate": "relationship or property",
            "value": "the value",
            "confidence": 0.0-1.0,
            "source_text": "exact phrase from user message",
            "temporal_context": "time reference if any, null otherwise"
        }}
    ],
    "risks": [
        {{
            "title": "short descriptive title",
            "description": "full description of the risk",
            "category": "financial|operational|compliance|strategic|market",
            "severity": "critical|high|medium|low|unknown",
            "cause": "what's causing this risk (if mentioned)",
            "impact": "potential impact (if mentioned)",
            "confidence": 0.0-1.0,
            "source_text": "exact phrase from user message"
        }}
    ],
    "metrics": [
        {{
            "metric_name": "name of metric (revenue, growth, churn, etc.)",
            "metric_type": "value|target|definition|comparison",
            "value": "numeric or text value (null if not specified)",
            "unit": "USD, %, count, etc. (null if not specified)",
            "time_period": "Q3 2024, last month, etc. (null if not specified)",
            "comparison": "change description if any (dropped 15%, increased 10%)",
            "definition": "how user defines this metric (if mentioned)",
            "confidence": 0.0-1.0,
            "source_text": "exact phrase from user message"
        }}
    ],
    "company_info": [
        {{
            "info_type": "name|industry|location|size|product|fiscal_year|structure|market",
            "value": "the information",
            "confidence": 0.0-1.0,
            "source_text": "exact phrase from user message"
        }}
    ],
    "preferences": [
        {{
            "preference_type": "visualization|detail_level|tone|frequency|format",
            "value": "the preference value",
            "confidence": 0.0-1.0,
            "source_text": "exact phrase from user message"
        }}
    ],
    "has_extractable_content": true|false
}}

Extract from the USER MESSAGE only. The assistant response is just for context."""


# ============================================================
# FACT EXTRACTOR
# ============================================================

class FactExtractor:
    """
    Extracts business facts from conversations using LLM.
    """
    
    def __init__(self, llm_client=None, model: str = "gpt-4o-mini"):
        """
        Initialize extractor.
        
        Args:
            llm_client: OpenAI client (or compatible). If None, uses rule-based extraction.
            model: Model to use for extraction
        """
        self.llm_client = llm_client
        self.model = model
        self.use_llm = llm_client is not None
    
    async def extract(
        self,
        user_message: str,
        assistant_response: str = "",
        context: Optional[Dict] = None
    ) -> ExtractionResult:
        """
        Extract facts from a conversation turn.
        
        Args:
            user_message: The user's message
            assistant_response: The assistant's response (for context)
            context: Optional context (previous facts, session info)
        
        Returns:
            ExtractionResult with all extracted information
        """
        # Skip extraction for very short or non-substantive messages
        if self._should_skip_extraction(user_message):
            return ExtractionResult(has_extractable_content=False)
        
        if self.use_llm:
            return await self._extract_with_llm(user_message, assistant_response)
        else:
            return self._extract_with_rules(user_message)
    
    async def _extract_with_llm(
        self,
        user_message: str,
        assistant_response: str
    ) -> ExtractionResult:
        """Extract using LLM"""
        prompt = EXTRACTION_USER_PROMPT.format(
            user_message=user_message,
            assistant_response=assistant_response
        )
        
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return self._parse_llm_response(response.choices[0].message.content)
        
        except Exception as e:
            print(f"LLM extraction error: {e}")
            # Fall back to rule-based extraction
            return self._extract_with_rules(user_message)
    
    def _extract_with_rules(self, message: str) -> ExtractionResult:
        """
        Rule-based extraction (no LLM needed).
        Less accurate but works offline.
        """
        result = ExtractionResult()
        message_lower = message.lower()
        
        # Extract company info
        result.company_info = self._extract_company_info_rules(message, message_lower)
        
        # Extract metrics
        result.metrics = self._extract_metrics_rules(message, message_lower)
        
        # Extract risks
        result.risks = self._extract_risks_rules(message, message_lower)
        
        # Extract preferences
        result.preferences = self._extract_preferences_rules(message, message_lower)
        
        # Extract general facts
        result.facts = self._extract_facts_rules(message, message_lower)
        
        result.has_extractable_content = bool(
            result.company_info or result.metrics or 
            result.risks or result.preferences or result.facts
        )
        
        return result
    
    def _extract_company_info_rules(self, message: str, message_lower: str) -> List[ExtractedCompanyInfo]:
        """Rule-based company info extraction"""
        info = []
        
        # Industry patterns
        industry_patterns = [
            (r"(?:we're|we are|i work at|i'm at) (?:a |an )?(.+?) company", "industry"),
            (r"(?:we're|we are) (?:in |in the )(.+?)(?:\s|industry|sector|business)", "industry"),
            (r"(?:our|the) company is (?:a |an )?(.+?) (?:company|business|firm)", "industry"),
        ]
        
        for pattern, info_type in industry_patterns:
            match = re.search(pattern, message_lower)
            if match:
                info.append(ExtractedCompanyInfo(
                    info_type=info_type,
                    value=match.group(1).strip(),
                    confidence=0.8,
                    source_text=match.group(0)
                ))
        
        # Location patterns
        location_patterns = [
            (r"(?:based in|headquartered in|hq in|located in) (.+?)(?:\.|,|$)", "location"),
            (r"(?:our|the) (?:office|headquarters|hq) (?:is |are )?in (.+?)(?:\.|,|$)", "location"),
        ]
        
        for pattern, info_type in location_patterns:
            match = re.search(pattern, message_lower)
            if match:
                info.append(ExtractedCompanyInfo(
                    info_type=info_type,
                    value=match.group(1).strip(),
                    confidence=0.85,
                    source_text=match.group(0)
                ))
        
        # Company name patterns
        name_patterns = [
            (r"(?:i work at|i'm at|we're|company is|company called) ([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*)", "name"),
        ]
        
        for pattern, info_type in name_patterns:
            match = re.search(pattern, message)  # Case-sensitive for names
            if match:
                info.append(ExtractedCompanyInfo(
                    info_type=info_type,
                    value=match.group(1).strip(),
                    confidence=0.9,
                    source_text=match.group(0)
                ))
        
        return info
    
    def _extract_metrics_rules(self, message: str, message_lower: str) -> List[ExtractedMetric]:
        """Rule-based metric extraction"""
        metrics = []
        
        # Metric value patterns
        value_patterns = [
            # Revenue/sales patterns
            (r"(?:revenue|sales) (?:was|were|is|are|of|at) \$?([\d,\.]+)\s*([mkb](?:illion)?)?", "revenue", "value"),
            (r"\$?([\d,\.]+)\s*([mkb](?:illion)?)? (?:in |of )?(?:revenue|sales)", "revenue", "value"),
            
            # Growth patterns
            (r"(?:growth|grew) (?:of |by |at )?([\d\.]+)%", "growth", "value"),
            (r"([\d\.]+)% (?:growth|increase)", "growth", "value"),
            
            # Margin patterns  
            (r"(?:margin|margins) (?:of |at |is |are )?([\d\.]+)%", "margin", "value"),
            
            # Churn patterns
            (r"(?:churn|churn rate) (?:of |at |is |are )?([\d\.]+)%", "churn", "value"),
        ]
        
        for pattern, metric_name, metric_type in value_patterns:
            match = re.search(pattern, message_lower)
            if match:
                value = match.group(1).replace(",", "")
                unit = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
                
                # Convert units
                if unit:
                    unit = unit.lower()
                    if unit.startswith("m"):
                        value = float(value) * 1000000
                        unit = "USD"
                    elif unit.startswith("b"):
                        value = float(value) * 1000000000
                        unit = "USD"
                    elif unit.startswith("k"):
                        value = float(value) * 1000
                        unit = "USD"
                
                metrics.append(ExtractedMetric(
                    metric_name=metric_name,
                    metric_type=metric_type,
                    value=float(value) if value else None,
                    unit=unit or ("%" if "%" in match.group(0) else "USD"),
                    confidence=0.85,
                    source_text=match.group(0)
                ))
        
        # Change/comparison patterns
        change_patterns = [
            (r"(?:revenue|sales|growth|margin) (?:dropped|fell|decreased|declined) (?:by )?([\d\.]+)%", "comparison"),
            (r"(?:revenue|sales|growth|margin) (?:increased|grew|rose|jumped) (?:by )?([\d\.]+)%", "comparison"),
        ]
        
        for pattern, metric_type in change_patterns:
            match = re.search(pattern, message_lower)
            if match:
                # Extract metric name from pattern
                metric_match = re.search(r"(revenue|sales|growth|margin)", match.group(0))
                metric_name = metric_match.group(1) if metric_match else "unknown"
                
                direction = "decreased" if any(w in match.group(0) for w in ["dropped", "fell", "decreased", "declined"]) else "increased"
                
                metrics.append(ExtractedMetric(
                    metric_name=metric_name,
                    metric_type=metric_type,
                    comparison=f"{direction} {match.group(1)}%",
                    confidence=0.9,
                    source_text=match.group(0)
                ))
        
        # Target patterns
        target_patterns = [
            (r"(?:target|targeting|goal|aiming for) (?:of |is |at )?([\d\.]+)%\s*(?:growth|increase)?", "target"),
            (r"(?:we |our )?(?:target|goal) (?:is |of )?\$?([\d,\.]+)", "target"),
        ]
        
        for pattern, metric_type in target_patterns:
            match = re.search(pattern, message_lower)
            if match:
                metrics.append(ExtractedMetric(
                    metric_name="target",
                    metric_type=metric_type,
                    value=match.group(1).replace(",", ""),
                    confidence=0.85,
                    source_text=match.group(0)
                ))
        
        # Time period extraction
        time_patterns = [
            (r"(?:in |for |during )?(q[1-4])(?: \d{4})?", "quarter"),
            (r"(?:in |for |during )?(\d{4})", "year"),
            (r"(?:last|this|next) (month|quarter|year)", "relative"),
        ]
        
        for metric in metrics:
            for pattern, _ in time_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    metric.time_period = match.group(1) if match.group(1) else match.group(0)
                    break
        
        return metrics
    
    def _extract_risks_rules(self, message: str, message_lower: str) -> List[ExtractedRisk]:
        """Rule-based risk extraction"""
        risks = []
        
        # Risk indicator patterns
        risk_patterns = [
            (r"(?:biggest|main|major|primary|key) risk (?:is |are )?(.+?)(?:\.|$)", "high"),
            (r"(?:worried|concerned) about (.+?)(?:\.|$)", "medium"),
            (r"(?:risk of|threat of) (.+?)(?:\.|$)", "medium"),
            (r"(.+?) is (?:killing|hurting|damaging) (?:our|the) (.+)", "high"),
        ]
        
        for pattern, default_severity in risk_patterns:
            match = re.search(pattern, message_lower)
            if match:
                description = match.group(1).strip()
                
                # Determine category
                category = "strategic"  # default
                if any(w in description for w in ["revenue", "cost", "margin", "profit", "financial", "budget", "price"]):
                    category = "financial"
                elif any(w in description for w in ["tariff", "regulation", "compliance", "legal", "audit"]):
                    category = "compliance"
                elif any(w in description for w in ["competition", "market", "competitor", "share"]):
                    category = "market"
                elif any(w in description for w in ["operation", "supply", "process", "system"]):
                    category = "operational"
                
                # Adjust severity based on language
                severity = default_severity
                if any(w in message_lower for w in ["critical", "urgent", "existential", "catastrophic"]):
                    severity = "critical"
                elif any(w in message_lower for w in ["biggest", "major", "significant", "serious"]):
                    severity = "high"
                
                risks.append(ExtractedRisk(
                    title=description[:50] + "..." if len(description) > 50 else description,
                    description=description,
                    category=category,
                    severity=severity,
                    confidence=0.75,
                    source_text=match.group(0)
                ))
        
        return risks
    
    def _extract_preferences_rules(self, message: str, message_lower: str) -> List[ExtractedPreference]:
        """Rule-based preference extraction"""
        preferences = []
        
        preference_patterns = [
            # Visualization preferences
            (r"(?:i |we )?prefer (?:to see |seeing )?(.+?)(?:charts?|graphs?|tables?|visuals?)", "visualization"),
            (r"(?:show|display|present) (?:it |them |this )?(?:as |in )?(?:a |an )?(.+?)(?:chart|graph|table)", "visualization"),
            
            # Detail level
            (r"(?:i |we )?(?:prefer|want|like) (?:more )?(?:detailed|brief|summary|concise)", "detail_level"),
            
            # Frequency
            (r"(?:i |we )?prefer (?:to see )?(daily|weekly|monthly|quarterly|annual)", "frequency"),
            
            # Format
            (r"(?:i |we )?(?:prefer|want|like) (.+?) format", "format"),
        ]
        
        for pattern, pref_type in preference_patterns:
            match = re.search(pattern, message_lower)
            if match:
                preferences.append(ExtractedPreference(
                    preference_type=pref_type,
                    value=match.group(1).strip() if match.groups() else match.group(0),
                    confidence=0.8,
                    source_text=match.group(0)
                ))
        
        return preferences
    
    def _extract_facts_rules(self, message: str, message_lower: str) -> List[ExtractedFact]:
        """Rule-based general fact extraction"""
        facts = []
        
        # Temporal events
        temporal_patterns = [
            (r"(?:we |i )?(?:launched|started|opened|began) (?:in |our )?(.+?) (?:in |on )?(\d{4}|\w+ \d{4})", "launched_in"),
            (r"(?:we |i )?(?:acquired|bought|merged with) (.+?) (?:in |on )?(\d{4}|\w+ \d{4})", "acquired"),
        ]
        
        for pattern, predicate in temporal_patterns:
            match = re.search(pattern, message_lower)
            if match:
                facts.append(ExtractedFact(
                    fact_type="temporal_event",
                    subject=match.group(1).strip(),
                    predicate=predicate,
                    value=match.group(2).strip(),
                    confidence=0.85,
                    source_text=match.group(0),
                    temporal_context=match.group(2).strip()
                ))
        
        # Relationships
        relationship_patterns = [
            (r"(.+?) (?:drives?|contributes?|accounts? for) ([\d\.]+%?) (?:of )?(?:our |the )?(.+)", "contributes_to"),
            (r"(.+?) reports? to (.+)", "reports_to"),
        ]
        
        for pattern, predicate in relationship_patterns:
            match = re.search(pattern, message_lower)
            if match:
                facts.append(ExtractedFact(
                    fact_type="relationship",
                    subject=match.group(1).strip(),
                    predicate=predicate,
                    value=f"{match.group(2)} of {match.group(3)}" if len(match.groups()) > 2 else match.group(2),
                    confidence=0.8,
                    source_text=match.group(0)
                ))
        
        return facts
    
    def _parse_llm_response(self, response: str) -> ExtractionResult:
        """Parse LLM JSON response into ExtractionResult"""
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            data = json.loads(response)
            
            return ExtractionResult(
                facts=[ExtractedFact(**f) for f in data.get("facts", [])],
                risks=[ExtractedRisk(**r) for r in data.get("risks", [])],
                metrics=[ExtractedMetric(**m) for m in data.get("metrics", [])],
                company_info=[ExtractedCompanyInfo(**c) for c in data.get("company_info", [])],
                preferences=[ExtractedPreference(**p) for p in data.get("preferences", [])],
                has_extractable_content=data.get("has_extractable_content", False)
            )
        
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return ExtractionResult(has_extractable_content=False)
        except Exception as e:
            print(f"Parse error: {e}")
            return ExtractionResult(has_extractable_content=False)
    
    def _should_skip_extraction(self, message: str) -> bool:
        """Check if message is too short or non-substantive"""
        message = message.strip()
        
        # Skip very short messages
        if len(message) < 15:
            return True
        
        # Skip common non-substantive patterns
        skip_patterns = [
            r"^(hello|hi|hey|thanks|thank you|ok|okay|got it|understood|yes|no|sure|please|help)[\.\!\?]?$",
            r"^(good|great|awesome|perfect|nice|cool)[\.\!\?]?$",
            r"^(what|how|when|where|why|who|which|can you|could you|would you)[\?\s]",  # Questions without content
        ]
        
        message_lower = message.lower()
        for pattern in skip_patterns:
            if re.match(pattern, message_lower):
                return True
        
        return False


# ============================================================
# EXTRACTION UTILITIES
# ============================================================

def convert_extraction_to_facts(extraction: ExtractionResult) -> List[Dict]:
    """
    Convert ExtractionResult to list of fact dictionaries
    for storage in BusinessKnowledgeMemory.
    """
    facts = []
    
    # Convert company info
    for info in extraction.company_info:
        facts.append({
            "fact_type": "company_info",
            "subject": "company",
            "predicate": info.info_type,
            "value": info.value,
            "confidence": info.confidence,
            "source_text": info.source_text
        })
    
    # Convert metrics
    for metric in extraction.metrics:
        facts.append({
            "fact_type": f"metric_{metric.metric_type}",
            "subject": metric.metric_name,
            "predicate": metric.metric_type,
            "value": {
                "value": metric.value,
                "unit": metric.unit,
                "time_period": metric.time_period,
                "comparison": metric.comparison,
                "definition": metric.definition
            },
            "confidence": metric.confidence,
            "source_text": metric.source_text
        })
    
    # Convert risks
    for risk in extraction.risks:
        facts.append({
            "fact_type": "risk",
            "title": risk.title,
            "description": risk.description,
            "category": risk.category,
            "severity": risk.severity,
            "cause": risk.cause,
            "impact": risk.impact,
            "confidence": risk.confidence,
            "source_text": risk.source_text
        })
    
    # Convert general facts
    for fact in extraction.facts:
        facts.append({
            "fact_type": fact.fact_type,
            "subject": fact.subject,
            "predicate": fact.predicate,
            "value": fact.value,
            "confidence": fact.confidence,
            "source_text": fact.source_text,
            "temporal_context": fact.temporal_context
        })
    
    # Convert preferences (these go to conversational memory)
    for pref in extraction.preferences:
        facts.append({
            "fact_type": "preference",
            "subject": "user",
            "predicate": pref.preference_type,
            "value": pref.value,
            "confidence": pref.confidence,
            "source_text": pref.source_text
        })
    
    return facts
