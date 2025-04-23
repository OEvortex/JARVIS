import requests
import json

class Hika:
    def __init__(
        self,
        timeout: int = 30,
        proxies: dict = {},
        x_hika: str = None,
        x_uid: str = None,
    ):    
        self.x_hika = x_hika
        self.x_uid = x_uid
        self.session = requests.Session()
        self.chat_endpoint = 'https://api.hika.fyi/api/kbase/web'
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'content-type': 'application/json',
            'origin': 'https://hika.fyi',
            'referer': 'https://hika.fyi/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
            'x-hika': self.x_hika,
            'x-uid': self.x_uid
        }
        self.session.headers.update(self.headers)
        self.session.proxies = proxies

    def ask(self, prompt: str, stream: bool = True, language: str = "en") -> dict:
        payload = {
            "stream": "true" if stream else "false",
            "keyword": prompt,
            "language": language
        }

        def for_stream():
            response = self.session.post(
                self.chat_endpoint,
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            streaming_text = ""
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if 'chunk' in data:
                            streaming_text += data['chunk']
                            self.last_response.update(dict(text=streaming_text))
                            yield data['chunk']
                    except json.JSONDecodeError:
                        continue

        def for_non_stream():
            return ''.join([chunk for chunk in for_stream()])

        return for_stream() if stream else for_non_stream()

    def chat(self, prompt: str, stream: bool = True) -> str:
        return self.ask(prompt, stream)

if __name__ == '__main__':
    from rich import print
    ai = Hika(x_hika="07fa2fe39db78dfa9bc93a7a23907b54df1762c35a211361249c6dee132b9486", x_uid="3IAll8DTVHugTYrHEKr0U")
    response = ai.chat(input(">>> "), stream=True)
    if isinstance(response, str):
        print(response)
    else:
        for chunk in response:
            print(chunk, end="", flush=True)