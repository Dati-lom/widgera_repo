import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping

from django.conf import settings
from openai import OpenAI
from openai import APIConnectionError, APIError, BadRequestError, RateLimitError

logger = logging.getLogger(__name__)


class LLMServiceError(RuntimeError):
    """Raised when the LLM service cannot fulfill a request."""


@dataclass
class LLMResponse:
    structured_data: Dict[str, Any]
    raw_text: str
    model: str
    usage: Dict[str, int]


class LLMService:
    
    def __init__(self,*,api_key=None ,base_url=None,default_model=None,) -> None:
        self._api_key = api_key or getattr(settings, 'OPENAI_API_KEY', '')
        self._base_url = base_url or getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1')
        self.default_model = default_model or getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        self._client = None

    #client init
    def _get_client(self) -> OpenAI:
        if not self._client:
            api_key = self._api_key or settings.OPENAI_API_KEY
            if not api_key:
                raise LLMServiceError('OPENAI_API_KEY is not configured')
            self._client = OpenAI(api_key=api_key, base_url=self._base_url)
        return self._client

    #returns structured field instructions
    def _build_field_instructions(self, fields: Iterable[Mapping[str, Any]]) -> str:
        lines: List[str] = []
        for field in fields or []:
            name = field.get('name') if isinstance(field, Mapping) else str(field)
            field_type = field.get('field_type', 'string') if isinstance(field, Mapping) else 'string'
            lines.append(f"- {name}: {field_type}")
        if not lines:
            lines.append('- response_text: string')
        return '\n'.join(lines)

    #build message using fields and image and text to then send to openai
    def _build_messages(self, prompt_text, field_instructions, image_url,) -> List[Dict[str, str]]:
        image_hint = f"An image has been uploaded. URL: {image_url}\n" if image_url else ''
        user_message = (
            f"{image_hint}Respond to the following prompt.\n"
            f"Prompt:\n{prompt_text.strip()}\n\n"
            "Return a JSON object that strictly follows these fields:\n"
            f"{field_instructions}.\nUse lower_snake_case keys and numbers for numeric fields."
        )
        return [
            {
                'role': 'system',
                'content': 'You are a structured data generator. Always respond with valid JSON.',
            },
            {
                'role': 'user',
                'content': user_message,
            },
        ]

    #build message and then send to openai
    def generate_structured_response(self, *, prompt_text, fields, image_url, model="gpt-5.1", temperature=0.7, max_tokens="5000",) -> LLMResponse:
        if not prompt_text or not prompt_text.strip():
            raise ValueError('PROMPT TEXT REQUIRED')

        normalized_fields = list(fields or [])
        field_instructions = self._build_field_instructions(normalized_fields)
        messages = self._build_messages(prompt_text, field_instructions, image_url)
        model_name = model or self.default_model

        try:
            logger.debug('SENDING TO MODEL %s', model_name)
            response = self._get_client().chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                # max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
        except (APIConnectionError, RateLimitError) as exc:
            logger.warning('CONNECTION OPENAI ERROR: %s', exc)
            raise LLMServiceError('CONNECTION OPENAI ERROR') from exc
        except (BadRequestError, APIError) as exc:
            logger.error('OPENAI REJECT: %s', exc)
            raise LLMServiceError('OPENAI REJECT CHECK FIELDS') from exc

        choice = response.choices[0]
        
        #gets raw cibteb and triees loading to json
        raw_content = choice.message.content or ''
        try:
            structured = json.loads(raw_content)
        except json.JSONDecodeError:
            logger.warning('RETURNED INVALID JSON')
            structured = {'raw_response': raw_content}

        usage = {
            'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0),
            'completion_tokens': getattr(response.usage, 'completion_tokens', 0),
            'total_tokens': getattr(response.usage, 'total_tokens', 0),
        }
        #give out response
        return LLMResponse(
            structured_data=structured,
            raw_text=raw_content,
            model=response.model or model_name,
            usage=usage,
        )


def get_llm_service() -> LLMService:
    return LLMService()


llm_service = LLMService()
