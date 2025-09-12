"""
LLM Processor - Process HTML content with Gemini to extract structured legal data
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os

logger = logging.getLogger(__name__)

class LLMProcessor:
    """Process legal HTML content with Google Gemini"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM processor
        
        Args:
            api_key: Google AI API key (optional, will try environment variable)
        """
        self.api_key = api_key or os.getenv('GOOGLE_AI_API_KEY')
        if not self.api_key:
            raise ValueError("Google AI API key is required. Set GOOGLE_AI_API_KEY environment variable or pass api_key parameter.")
        
        genai.configure(api_key=self.api_key)
        
        # Configure the model
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.1,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        logger.info("LLM Processor initialized with Gemini")
    
    async def process_legal_html(self, html_content: str, query: str) -> Dict:
        """
        Process HTML content and extract structured legal data
        
        Args:
            html_content: Raw HTML content from legal search
            query: Original search query
            
        Returns:
            Dict with structured legal data
        """
        try:
            prompt = self._create_extraction_prompt(html_content, query)
            
            # Generate response
            response = await self._generate_with_retry(prompt)
            
            # Parse JSON response
            try:
                structured_data = json.loads(response)
                logger.info(f"Successfully processed legal HTML for query: {query}")
                return structured_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.debug(f"Raw response: {response[:500]}...")
                
                # Try to extract JSON from response
                structured_data = self._extract_json_from_response(response)
                if structured_data:
                    return structured_data
                
                # Fallback: return error structure
                return self._create_error_response(f"JSON parsing failed: {e}", query)
                
        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            return self._create_error_response(str(e), query)
    
    def _create_extraction_prompt(self, html_content: str, query: str) -> str:
        """Create prompt for extracting structured data from HTML"""
        return f"""
You are a legal data extraction specialist. Extract structured information from Singapore legal search results.

SEARCH QUERY: "{query}"

INSTRUCTIONS:
1. Extract case law and parliamentary (Hansard) records from the HTML
2. Identify working links that can be accessed by front-end clients
3. Return ONLY valid JSON - no explanations or markdown
4. If a section has no results, return empty arrays

REQUIRED JSON STRUCTURE:
{{
    "caseLaw": [
        {{
            "caseName": "string",
            "date": "YYYY-MM-DD",
            "citation": "string", 
            "workingLinks": ["url1", "url2"],
            "relevance": "string",
            "source": "string"
        }}
    ],
    "hansardRecords": [
        {{
            "title": "string",
            "date": "YYYY-MM-DD",
            "sessionDetails": "string", 
            "link": "string",
            "keyContent": "string",
            "source": "string"
        }}
    ],
    "searchMetadata": {{
        "totalResults": number,
        "searchTime": "string",
        "searchQuery": "{query}",
        "processingStatus": "success"
    }}
}}

LINK GUIDELINES:
- For case law: prefer Singapore Law Watch, Singapore Judiciary, or CommonLII links
- For Hansard: use sprs.parl.gov.sg links
- Convert JavaScript links to working HTTP URLs where possible
- If original links don't work, suggest alternative access methods

HTML CONTENT:
{html_content[:15000]}  
"""
    
    async def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Generate response with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                
                if response.text:
                    return response.text.strip()
                else:
                    raise Exception("Empty response from model")
                    
            except Exception as e:
                logger.warning(f"LLM generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception("All LLM generation attempts failed")
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Try to extract JSON from response that might have extra text"""
        try:
            # Look for JSON block in response
            start_idx = response.find('{')
            if start_idx == -1:
                return None
            
            # Find the matching closing brace
            brace_count = 0
            end_idx = start_idx
            
            for i, char in enumerate(response[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
            
        except Exception as e:
            logger.warning(f"Failed to extract JSON from response: {e}")
            return None
    
    def _create_error_response(self, error_message: str, query: str) -> Dict:
        """Create standardized error response"""
        return {
            "caseLaw": [],
            "hansardRecords": [],
            "searchMetadata": {
                "totalResults": 0,
                "searchTime": "N/A",
                "searchQuery": query,
                "processingStatus": "error",
                "errorMessage": error_message
            }
        }
    
    async def process_batch(self, html_contents: List[str], queries: List[str]) -> List[Dict]:
        """Process multiple HTML contents in batch"""
        results = []
        
        for html_content, query in zip(html_contents, queries):
            try:
                result = await self.process_legal_html(html_content, query)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch processing failed for query '{query}': {e}")
                results.append(self._create_error_response(str(e), query))
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        return results
    
    def test_connection(self) -> bool:
        """Test if the LLM connection is working"""
        try:
            test_prompt = "Return only this JSON: {\"test\": \"success\"}"
            response = self.model.generate_content(test_prompt)
            
            if response.text and "success" in response.text:
                logger.info("LLM connection test successful")
                return True
            else:
                logger.warning("LLM connection test returned unexpected response")
                return False
                
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False

# Convenience function
async def process_legal_content(html_content: str, query: str, api_key: Optional[str] = None) -> Dict:
    """Process legal HTML content and return structured data"""
    processor = LLMProcessor(api_key)
    return await processor.process_legal_html(html_content, query)