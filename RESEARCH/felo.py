import re
import requests
from uuid import uuid4
import json
from typing import Dict, Any, Iterator, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class FeloResponse:
    """Data class to store Felo AI response information"""
    text: str
    search_uuid: str
    raw_response: Optional[Dict[str, Any]] = None

class ResponseFormatter(ABC):
    """Abstract base class for Felo response formatting"""
    @abstractmethod
    def format_response(self, response: FeloResponse) -> str:
        pass

class DefaultResponseFormatter(ResponseFormatter):
    """Default implementation of Felo response formatting"""
    def format_response(self, response: FeloResponse) -> str:
        # Clean up response by removing citation markers like [[1]]
        return re.sub(r'\[\[\d+\]\]', '', response.text)

class Felo:
    """Main service class for interacting with Felo AI research API"""
    def __init__(
        self,
        timeout: int = 30,
        proxies: dict = {},
        history_offset: int = 10250,
        formatter: ResponseFormatter = DefaultResponseFormatter()
    ):
        self.session = requests.Session()
        self.chat_endpoint = "https://api.felo.ai/search/threads"
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "content-type": "application/json",
        }
        self.session.headers.update(self.headers)
        self.history_offset = history_offset
        self.session.proxies = proxies
        self.formatter = formatter

    def _prepare_payload(self, query: str) -> Dict[str, Any]:
        """Prepare the payload for the API request"""
        return {
            "query": query,
            "search_uuid": uuid4().hex,
            "search_options": {"langcode": "en-US"},
            "search_video": True,
        }

    def ask(self, query: str, stream: bool = False, raw: bool = False) -> Union[str, Iterator[str]]:
        """
        Send a research query to Felo AI
        
        Args:
            query (str): The research question to ask
            stream (bool): Whether to stream the response
            raw (bool): Whether to return raw API responses
            
        Returns:
            Union[str, Iterator[str]]: Research results as string or stream
        """
        try:
            payload = self._prepare_payload(query)
            
            if stream:
                return self._handle_streaming_response(payload, raw)
            else:
                return self._handle_standard_response(payload)
        except Exception as e:
            return f"Error querying Felo AI: {str(e)}"

    def _handle_streaming_response(self, payload: Dict[str, Any], raw: bool = False) -> Iterator[str]:
        """Handle streaming response from Felo API"""
        response = self.session.post(
            self.chat_endpoint, json=payload, stream=True, timeout=self.timeout
        )
        streaming_text = ""
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data:'):
                try:
                    data = json.loads(line[5:].strip())
                    if 'text' in data['data']:
                        new_text = data['data']['text']
                        delta = new_text[len(streaming_text):]
                        streaming_text = new_text
                        self.last_response.update(dict(text=streaming_text))
                        yield delta if not raw else line
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    yield f"Error processing stream: {str(e)}"

    def _handle_standard_response(self, payload: Dict[str, Any]) -> str:
        """Handle standard (non-streaming) response from Felo API"""
        response_text = ''.join([chunk for chunk in self._handle_streaming_response(payload)])
        
        felo_response = FeloResponse(
            text=response_text,
            search_uuid=payload["search_uuid"],
            raw_response=self.last_response
        )
        
        return self.formatter.format_response(felo_response)

    def chat(self, prompt: str, stream: bool = False) -> Union[str, Iterator[str]]:
        """
        Send a chat prompt to Felo AI
        
        Args:
            prompt (str): The research question to ask
            stream (bool): Whether to stream the response
            
        Returns:
            Union[str, Iterator[str]]: Research results as string or stream
        """
        return self.ask(prompt, stream)


# Example usage
if __name__ == '__main__':
    from rich import print
    ai = Felo()
    response = ai.chat(input(">>> "), stream=True)
    if isinstance(response, str):
        print(response)
    else:
        for chunk in response:
            print(chunk, end="", flush=True)