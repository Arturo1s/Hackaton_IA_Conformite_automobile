import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()  # make sure .env is loaded first

HF_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

if HF_KEY is None:
    raise ValueError("HF_API_KEY missing in .env")

client = InferenceClient(model=HF_MODEL, token=HF_KEY)

def generate_answer(prompt: str, max_tokens: int = 3000):
    """Generate a response using HuggingFace chat-completion"""
    response = client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.25,
        top_p=0.95,
    )
    return response.choices[0].message['content']


# Only run test code if executed directly, not on import
if __name__ == "__main__":
    test = generate_answer("Hello")
    print(test)
