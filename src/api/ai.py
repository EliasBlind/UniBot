import ollama

def _request(model: str, message: str) -> str:
    response = ollama.chat(model=f'{model}', messages=[
        {
            'role': 'user',
            'content': f'{message}'
        },
    ])
    return response['message']['content']

def quik_request(message: str) -> str:
    return _request('llama3.2:1b', message)

def thinking_request(message: str) -> str:
    return _request('deepseek-coder:6.7b', message)
