"""
LLM agent for processing financial documents
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import openai
import json
from backend.config import settings


class FinOpsAgent:
    """Main agent for financial document analysis"""
    
    def __init__(self, api_key: str = None, model: str = None):
        if api_key is None:
            api_key = settings.openai_api_key
        if model is None:
            model = settings.openai_model
        
        # Only initialize client if API key is provided
        if api_key and api_key.strip():
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None
        self.model = model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens
        
        # Load prompts
        self.prompts_dir = Path(__file__).parent / "prompts"
        self._load_prompts()
    
    def _load_prompts(self):
        """Load prompt templates"""
        self.kpi_prompt = self._read_prompt("kpi_prompt.txt")
        self.risk_prompt = self._read_prompt("risk_prompt.txt")
        self.memo_prompt = self._read_prompt("memo_prompt.txt")
        self.qa_prompt = self._read_prompt("qa_prompt.txt")
    
    def _read_prompt(self, filename: str) -> str:
        """Read prompt from file"""
        prompt_path = self.prompts_dir / filename
        if prompt_path.exists():
            return prompt_path.read_text()
        return ""
    
    def _call_llm(self, prompt: str, system_message: str = None) -> str:
        """Make LLM API call"""
        if not self.client:
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            # Check for quota errors
            if 'quota' in error_str.lower() or 'insufficient_quota' in error_str.lower() or 'exceeded' in error_str.lower():
                raise ValueError(f"OpenAI API quota exceeded. Please check your billing at https://platform.openai.com/account/billing. Error: {error_str}")
            # Re-raise other errors
            raise
    
    def extract_kpis(self, document: str) -> Dict[str, Any]:
        """Extract KPIs from financial documents"""
        if not self.client:
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
        
        prompt = self.kpi_prompt.format(document=document[:50000])  # Limit document size
        
        response = self._call_llm(
            prompt,
            system_message="You are a financial analyst expert at extracting KPIs from financial documents. Always return valid JSON."
        )
        
        # Try to parse JSON from response
        try:
            # Extract JSON from response if it's wrapped in markdown
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            
            kpis = json.loads(response)
            return kpis
        except json.JSONDecodeError:
            # Fallback: return as text
            return {"raw_response": response, "error": "Could not parse as JSON"}
    
    def summarize_risks(self, document: str) -> Dict[str, List[str]]:
        """Summarize risks from financial documents"""
        if not self.client:
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
        
        prompt = self.risk_prompt.format(document=document[:50000])
        
        response = self._call_llm(
            prompt,
            system_message="You are a risk analyst expert. Structure your response clearly with categories."
        )
        
        # Try to parse structured response
        risks = {
            "market_risks": [],
            "operational_risks": [],
            "financial_risks": [],
            "regulatory_risks": [],
            "competitive_risks": [],
            "other_risks": []
        }
        
        # Simple parsing - look for category headers
        lines = response.split('\n')
        current_category = None
        
        for line in lines:
            line_lower = line.lower().strip()
            if 'market risk' in line_lower or line_lower.startswith('1.'):
                current_category = "market_risks"
            elif 'operational risk' in line_lower or line_lower.startswith('2.'):
                current_category = "operational_risks"
            elif 'financial risk' in line_lower or line_lower.startswith('3.'):
                current_category = "financial_risks"
            elif 'regulatory risk' in line_lower or line_lower.startswith('4.'):
                current_category = "regulatory_risks"
            elif 'competitive risk' in line_lower or line_lower.startswith('5.'):
                current_category = "competitive_risks"
            elif line.strip() and current_category and not line.strip().startswith('-'):
                risks[current_category].append(line.strip())
            elif line.strip().startswith('-') and current_category:
                risks[current_category].append(line.strip().lstrip('- ').strip())
        
        # If no structured parsing worked, put everything in other_risks
        if not any(risks.values()):
            risks["other_risks"] = [response]
        
        return risks
    
    def compare_filings(self, filing1: str, filing2: str, period1: str = "Period 1", period2: str = "Period 2") -> Dict[str, Any]:
        """Compare filings between years"""
        if not self.client:
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
        
        comparison_prompt = f"""Compare two financial filings and identify key changes.

Filing 1 ({period1}):
{filing1[:25000]}

Filing 2 ({period2}):
{filing2[:25000]}

Provide a comparison in the following format:
1. Revenue changes
2. Profitability changes
3. Key metric changes
4. Risk changes
5. Overall summary

Format as JSON with keys: revenue_changes, profitability_changes, metric_changes, risk_changes, summary"""
        
        response = self._call_llm(
            comparison_prompt,
            system_message="You are a financial analyst expert at comparing financial documents. Return structured comparisons."
        )
        
        # Try to parse JSON
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            
            comparison = json.loads(response)
            comparison["period1"] = period1
            comparison["period2"] = period2
            return comparison
        except json.JSONDecodeError:
            return {
                "period1": period1,
                "period2": period2,
                "summary": response,
                "error": "Could not parse structured comparison"
            }
    
    def generate_memo(self, context: Dict[str, Any]) -> str:
        """Generate investment memo"""
        if not self.client:
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
        
        company_name = context.get("company_name", "Company")
        period = context.get("period", "Current Period")
        kpis = context.get("kpis", {})
        risks = context.get("risks", {})
        additional_context = context.get("context", "")
        
        # Format KPIs and risks as strings
        kpis_str = json.dumps(kpis, indent=2) if isinstance(kpis, dict) else str(kpis)
        risks_str = json.dumps(risks, indent=2) if isinstance(risks, dict) else str(risks)
        
        prompt = self.memo_prompt.format(
            company_name=company_name,
            period=period,
            kpis=kpis_str,
            risks=risks_str,
            context=additional_context
        )
        
        response = self._call_llm(
            prompt,
            system_message="You are a senior investment analyst. Write professional, concise investment memos."
        )
        
        return response
    
    def answer_question(self, question: str, context: str) -> str:
        """Answer a question using provided context"""
        if not self.client:
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
        
        prompt = self.qa_prompt.format(
            context=context[:30000],  # Limit context size
            question=question
        )
        
        response = self._call_llm(
            prompt,
            system_message="You are a financial analyst assistant. Answer questions accurately based on the provided context."
        )
        
        return response

