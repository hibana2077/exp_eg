from openai import OpenAI
import os

API_KEY = os.getenv("OPENROUTE_API_KEY", "sk-")

def llm_completion(additional_text:str, question:str)->str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
    )

    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
            "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
        },
        extra_body={},
        # model="moonshotai/kimi-vl-a3b-thinking:free",
        # model="google/gemini-2.5-pro-exp-03-25:free",
        model="mistralai/mistral-nemo",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are a helpful assistant that developed by Cathay, DDT team."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "<rag-data>" + additional_text + "</rag-data>"
                    },
                    {
                        "type": "text",
                        "text": "<question>" + question + "</question>"
                    }
                ]
            }
        ]
    )
    return completion.choices[0].message.content