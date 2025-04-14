from openai import OpenAI
import os
import time

API_KEY = os.getenv("OPENROUTE_API_KEY", "sk-")

def llm_completion(additional_text:str, question:str, max_retries=3)->str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
    )
    
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            completion = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
                    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
                },
                extra_body={},
                # model="moonshotai/kimi-vl-a3b-thinking:free",
                model="google/gemini-2.5-pro-exp-03-25:free",
                # model="mistralai/mistral-nemo",
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
            
            # Check if completion and its properties exist before accessing them
            if completion and completion.choices and completion.choices[0] and completion.choices[0].message:
                return completion.choices[0].message.content
            else:
                raise TypeError("Incomplete response received")
                
        except (TypeError, AttributeError) as e:
            retry_count += 1
            if retry_count >= max_retries:
                return f"Error after {max_retries} attempts: {str(e)}"
            print(f"Attempt {retry_count} failed: {str(e)}. Retrying...")
            time.sleep(2)  # Wait 2 seconds before retrying
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    return "Failed to get a response after multiple attempts"