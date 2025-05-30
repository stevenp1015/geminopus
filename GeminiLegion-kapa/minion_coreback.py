# minion_core.py
import re
import logging
from typing import Dict, Any, Optional, Tuple
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse, Content, Part

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MinionAgent:
    def __init__(self, minion_id: str, name: str, model_id: str, persona_prompt: str, temperature: float = 0.7):
        self.minion_id = minion_id
        self.name = name
        self.model_id = model_id
        self.persona_prompt = persona_prompt
        self.temperature = temperature
        
        self.opinion_scores: Dict[str, int] = {settings.LEGION_COMMANDER_NAME: 50}
        self.last_diary: Optional[str] = None
        
        if settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                # Construct system instructions once for the life of the agent, potentially.
                # However, previous_diary changes, so it needs to be dynamic.
                # self.base_system_instructions = settings.get_emotional_engine_prompt(
                #     minion_name=self.name,
                #     persona_prompt=self.persona_prompt,
                #     previous_diary=self.last_diary # This makes it dynamic per call
                # )
                # self.model = genai.GenerativeModel(
                #     model_name=self.model_id,
                #     # system_instruction will be set per call due to dynamic diary
                # )
            except Exception as e:
                logger.error(f"Minion {self.name}: Failed to configure Gemini: {e}")
                # self.model = None # type: ignore
        else:
            logger.warning(f"Minion {self.name}: GEMINI_API_KEY not available. LLM calls will be mocked/fail.")
            # self.model = None # type: ignore

        logger.info(f"Minion Agent {self.name} (ID: {self.minion_id}) initialized. Model: {self.model_id}")

    def _get_current_system_instructions(self) -> Content:
        """Generate system instructions including current state."""
        system_instruction = settings.get_emotional_engine_prompt(
            minion_name=self.name,
            persona_prompt=self.persona_prompt,
            previous_diary=self.last_diary
        )
        return Content(
            role="model",
            parts=[Part.from_text(system_instruction)]
        )

    async def process_message(
        self,
        message: str,
        sender_name: str,
        channel_name: str,
        channel_history: list[dict[str, Any]]
    ) -> Tuple[str, Optional[str]]: # Returns (spoken_response, full_llm_response_including_diary)
        
        if not settings.GEMINI_API_KEY: # Or self.model is None
            logger.error(f"Minion {self.name}: GEMINI_API_KEY not set or model not initialized. Cannot process message.")
            return "I am currently unable to process your request due to an internal configuration error.", None

        try:
            # Format channel history for the prompt
            channel_history_str = "\n".join(
                f"{msg['sender']}: {msg['content']}" 
                for msg in channel_history
            )

            # Get current system instructions with updated diary
            system_instruction = self._get_current_system_instructions()
            
            # Initialize the model with current system instructions
            model = genai.GenerativeModel(
                model_name=self.model_id,
                system_instruction=system_instruction
            )
            
            # Create the chat session
            chat = model.start_chat(history=[])
            
            # Prepare the user message with context
            user_message = f"""
            Channel: {channel_name}
            Sender: {sender_name}
            Message: {message}
            
            Channel History:
            {channel_history_str}
            """
            
            # Send the message and get response
            response = await chat.send_message_async(user_message)
            
            # Extract the response text
            response_text = response.text
            
            # Update the last diary entry (this is a simplified version)
            # In a real implementation, you'd parse the response to extract the diary portion
            self.last_diary = f"[Internal Diary - {self.name}] {response_text[:200]}..."
            
            # For now, just return the response as is
            return response_text, response_text
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(f"Minion {self.name}: {error_msg}")
            return f"I encountered an error while processing your message: {str(e)}", None
