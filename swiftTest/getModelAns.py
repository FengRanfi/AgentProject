from openai import OpenAI

client = OpenAI(
    api_key='EMPTY',
    base_url=f'http://127.0.0.1:8000/v1',
)
model = client.models.list().data[0].id
print(f'model: {model}')

messages = [{'role': 'user', 'content': [
    {'type': 'text', 'text': '你好'}
]}]

resp = client.chat.completions.create(model=model, messages=messages, max_tokens=512, temperature=0)
query = messages[0]['content']
response = resp.choices[0].message.content
print(f'query: {query}')
print(f'response: {response}')