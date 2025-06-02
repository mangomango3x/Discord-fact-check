import json
import os
import logging
from openai import OpenAI
import google.generativeai as genai

logger = logging.getLogger(__name__)

class AIClient:
    """Client for AI-powered analysis with multiple AI service fallbacks"""
    
    def __init__(self):
        # Initialize API clients and models
        self.pawan_api_key = os.getenv("PAWAN_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Primary: PawanOsman ChatGPT API
        if self.pawan_api_key:
            self.primary_client = OpenAI(
                api_key=self.pawan_api_key,
                base_url="https://api.pawan.krd/v1"
            )
            self.primary_model = "gpt-3.5-turbo"
            logger.info("Using PawanOsman ChatGPT API as primary")
        else:
            self.primary_client = None
            
        # Secondary: OpenAI API
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.openai_model = "gpt-4o"
            logger.info("OpenAI API available as secondary")
        else:
            self.openai_client = None
            
        # Tertiary: Google Gemini API
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Google Gemini API available as tertiary")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini API: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None
            
        # Check if at least one API is available
        if not any([self.primary_client, self.openai_client, self.gemini_model]):
            logger.error("No API keys found. Please provide PAWAN_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY")
            raise ValueError("At least one AI API key is required")
    
    async def analyze_statement(self, statement):
        """
        Analyze a statement for misinformation and provide factual information
        
        Args:
            statement (str): The statement to analyze
            
        Returns:
            dict: Analysis results including credibility, confidence, analysis, and facts
        """
        try:
            prompt = f"""
            Analyze the following statement for factual accuracy and provide detailed information to expose any misinformation:

            Statement: "{statement}"

            Please provide a comprehensive analysis in JSON format with the following structure:
            {{
                "credibility": <float 0-1 representing how credible the statement is>,
                "confidence": <float 0-1 representing confidence in this analysis>,
                "analysis": "<detailed analysis explaining why the statement is true/false>",
                "facts": "<key factual information that counters misinformation or supports truth>",
                "category": "<category of the statement: Scientific, Political, Health, Historical, Technology, Social, Economic, Environmental, or Unknown>",
                "misinformation_detected": <boolean indicating if misinformation was found>
            }}

            Be thorough, factual, and cite reasoning based on scientific consensus and reliable sources.
            """
            
            response = await self._make_request_with_fallback(prompt)
            if response:
                return json.loads(response)
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing statement: {e}")
            return None
    
    async def rate_truthiness(self, statement):
        """
        Rate the truthiness of a statement as a percentage
        
        Args:
            statement (str): The statement to rate
            
        Returns:
            dict: Truthiness rating with percentage and reasoning
        """
        try:
            prompt = f"""
            Rate the truthiness/credibility of the following statement as a percentage from 0-100:

            Statement: "{statement}"

            Provide your analysis in JSON format with the following structure:
            {{
                "truthiness_percentage": <integer 0-100 representing likelihood of being true>,
                "confidence": <float 0-1 representing confidence in this rating>,
                "reasoning": "<detailed explanation of why you gave this rating>",
                "category": "<category: Scientific, Political, Health, Historical, Technology, Social, Economic, Environmental, or Unknown>",
                "key_factors": ["<factor1>", "<factor2>", "<factor3>"],
                "evidence_quality": "<assessment of available evidence: Strong, Moderate, Weak, or Insufficient>"
            }}

            Consider:
            - Scientific consensus and peer-reviewed research
            - Logical consistency and plausibility
            - Source reliability and verification
            - Historical accuracy and context
            - Potential for bias or manipulation

            Be precise with your percentage and provide clear reasoning.
            """
            
            response = await self._make_request_with_fallback(prompt)
            if response:
                return json.loads(response)
            return None
            
        except Exception as e:
            logger.error(f"Error rating truthiness: {e}")
            return None
    
    async def analyze_context(self, original_message, reply_context):
        """
        Analyze a message in context of a reply for fact-checking
        
        Args:
            original_message (str): The original message being fact-checked
            reply_context (str): The context from the reply
            
        Returns:
            dict: Contextual analysis results
        """
        try:
            prompt = f"""
            Analyze the following message for misinformation, considering the context provided:

            Original Message: "{original_message}"
            Reply Context: "{reply_context}"

            Provide analysis in JSON format:
            {{
                "needs_fact_check": <boolean indicating if fact-checking is needed>,
                "credibility": <float 0-1>,
                "confidence": <float 0-1>,
                "analysis": "<contextual analysis>",
                "context_relevance": <float 0-1 indicating how relevant the context is>,
                "recommended_action": "<suggested response: fact-check, clarify, ignore, or investigate>"
            }}
            """
            
            response = await self._make_request_with_fallback(prompt)
            if response:
                return json.loads(response)
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
            return None
    
    async def analyze_with_community_context(self, statement, conversation_context, community_id=None):
        """
        Enhanced analysis with conversation and community context
        
        Args:
            statement (str): The statement to analyze
            conversation_context (list): Recent conversation messages
            community_id (str): Community identifier for pattern analysis
            
        Returns:
            dict: Enhanced analysis with community awareness
        """
        try:
            context_str = ""
            if conversation_context:
                context_str = "\nRecent conversation context:\n"
                for msg in conversation_context[-3:]:  # Last 3 messages
                    context_str += f"- {msg.get('author', 'User')}: {msg.get('content', '')[:100]}...\n"
            
            prompt = f"""
            Analyze the following statement for misinformation with enhanced community context awareness:

            Statement: "{statement}"
            {context_str}
            Community ID: {community_id or 'Unknown'}

            Consider:
            1. The statement's factual accuracy
            2. Potential for community harm or division
            3. Likelihood of viral spread in Discord communities
            4. Conversation context and relevance
            5. Urgency of intervention needed
            6. Common misinformation patterns in online communities

            Provide comprehensive analysis in JSON format:
            {{
                "truthiness_percentage": <integer 0-100>,
                "confidence": <float 0-1>,
                "reasoning": "<detailed contextual analysis>",
                "category": "<Scientific, Political, Health, Historical, Technology, Social, Economic, Environmental, or Unknown>",
                "urgency_level": "<low, medium, high, or critical>",
                "spread_risk": "<low, medium, or high - likelihood of viral spread>",
                "community_impact": "<potential impact on community dynamics>",
                "intervention_needed": <boolean>,
                "similar_claims_detected": <boolean - if this resembles common misinformation>,
                "emotional_manipulation": <float 0-1 - level of emotional manipulation detected>,
                "context_relevance": <float 0-1 - how relevant conversation context is>,
                "recommended_response": "<immediate, delayed, monitor, or ignore>",
                "key_concerns": ["<concern1>", "<concern2>", "<concern3>"],
                "fact_check_priority": "<high, medium, or low>"
            }}

            Be especially vigilant for:
            - Health misinformation that could cause harm
            - Political misinformation that could increase polarization
            - Conspiracy theories that typically spread in online communities
            - False claims that exploit current events or fears
            - Information that contradicts scientific consensus
            """
            
            response = await self._make_request_with_fallback(prompt)
            if response:
                return json.loads(response)
            return None
            
        except Exception as e:
            logger.error(f"Error in community context analysis: {e}")
            return None
    

    
    async def _make_request_with_fallback(self, prompt):
        """Make AI request with automatic fallback between services"""
        
        # Try PawanOsman first
        if self.primary_client:
            try:
                logger.info("Attempting request with PawanOsman API")
                response = self.primary_client.chat.completions.create(
                    model=self.primary_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert fact-checker and misinformation analyst. "
                            "Provide accurate, well-reasoned analysis based on scientific consensus, "
                            "reliable sources, and logical reasoning. Always respond in valid JSON format."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=1500
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"PawanOsman API failed: {e}")
        
        # Try OpenAI as secondary
        if self.openai_client:
            try:
                logger.info("Falling back to OpenAI API")
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert fact-checker and misinformation analyst. "
                            "Provide accurate, well-reasoned analysis based on scientific consensus, "
                            "reliable sources, and logical reasoning. Always respond in valid JSON format."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=1500
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenAI API failed: {e}")
        
        # Try Gemini as tertiary
        if self.gemini_model:
            try:
                logger.info("Falling back to Google Gemini API")
                
                # Modify prompt for Gemini to ensure clean JSON output
                gemini_prompt = f"""
                {prompt}
                
                CRITICAL INSTRUCTIONS:
                - Respond ONLY with a valid JSON object
                - Do NOT include any markdown formatting (no ```json or ```)
                - Do NOT include any explanations before or after the JSON
                - Do NOT include any additional text or commentary
                - Start your response directly with {{ and end with }}
                """
                
                response = self.gemini_model.generate_content(gemini_prompt)
                
                # Clean the response more thoroughly
                response_text = response.text.strip()
                
                # Remove common markdown formatting
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                elif response_text.startswith('```'):
                    response_text = response_text[3:]
                    
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                    
                response_text = response_text.strip()
                
                # Find the JSON object boundaries
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    response_text = response_text[start_idx:end_idx + 1]
                
                return response_text
            except Exception as e:
                logger.warning(f"Gemini API failed: {e}")
        
        logger.error("All AI services failed")
        return None
    
    async def generate_summary(self, text, max_length=500):
        """
        Generate a summary of text content
        
        Args:
            text (str): Text to summarize
            max_length (int): Maximum length of summary
            
        Returns:
            str: Summary text
        """
        try:
            prompt = f"""
            Summarize the following text in {max_length} characters or less, focusing on key facts and important information:

            Text: "{text}"

            Provide a clear, concise summary that preserves the most important information.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text
