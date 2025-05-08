from openai import OpenAI
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("OPENROUTE_API_KEY", "sk-")
LLM_MODEL = os.getenv("LLM_MODEL", "thudm/glm-z1-32b:free")

def llm_completion(additional_text:str, rag_data_img:list[str], question:str, max_retries=3)->str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
    )
    
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            completion = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://github.com/hibana2077/exp_eg",
                    "X-Title": "Data Engine",
                },
                extra_body={},
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": "You are Ai-Fa, an AI assistant developed by Cathay's Digital, Data, and Technology (DDT) team. Respond concisely and accurately, citing resource page numbers alongside your answers. Respond language should be based on user question. If you cannot find the answer, say 'I don't know'."
                            },
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
                                "type": "image_url",
                                "image_url":{
                                    "url": f"data:image/jpeg;base64,{rag_data_img[0]}",
                                }
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
                logger.error("Incomplete response structure")
                # Log the response for debugging
                logger.error(f"Response: {completion}")
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