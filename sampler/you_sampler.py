import time
from typing import Any
import httpx
import uuid

from eval_types import MessageList, SamplerBase

class YouSampler(SamplerBase):
    """Sample from You's smart chat API endpoint"""
    
    def __init__(
        self,
        api_key: str,
        max_retries: int = 3,
        base_url: str = "https://chat-api.you.com",
    ):
        self.api_key = api_key
        self.max_retries = max_retries
        self.client = httpx.Client(
            base_url=base_url,
            headers={"X-API-Key": api_key},
            timeout=60.0,
        )

    def _handle_text(self, text: str):
        return {"type": "text", "text": text}

    def _pack_message(self, role: str, content: Any):
        return {"role": str(role), "content": content}

    def __call__(self, message_list: MessageList) -> str:
        query = self.__extract_query_from_messages__(message_list)
        
        payload = {
            "query": query,
            "chat_id": str(uuid.uuid4()),
            "instructions": "" 
        }

        trial = 0
        while True:
            try:
                response = self.client.post("/smart", json=payload)
                data = response.json()
                if response.status_code != 200:
                    print(f"Error {response.status_code}: {data.get('error', 'Unknown error')}, query: {query}")
                    raise httpx.HTTPStatusError(
                        f"Error {response.status_code}: {data.get('error', 'Unknown error')}", 
                        request=response.request, 
                        response=response
                    )
                return data["answer"]
                
            except Exception as e:
                if trial >= self.max_retries:
                    print(f"Failed after {self.max_retries} retries: {str(e)}")
                    return "Failed to get response"

                trial += 1
                exception_backoff = 2 ** (1+trial)
                print(f"Attempt {trial}/{self.max_retries} failed: {str(e)}. Retrying in {exception_backoff}s...")
                time.sleep(exception_backoff)


    def close(self):
        """Cleanup resources"""
        self.client.close()