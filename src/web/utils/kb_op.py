import requests
import os

# Base URL for the API
BASE_URL = os.getenv("BACKEND_SERVER", "http://localhost:8000")

def create_knowledge_base(name, description, icon, owner):
    """
    Create a new knowledge base.
    
    Parameters:
    - name: Knowledge base name
    - description: Knowledge base description
    - icon: Knowledge base icon
    - owner: Owner username
    
    Returns:
    - API response
    """
    endpoint = f"{BASE_URL}/new_kb"
    
    payload = {
        "name": name,
        "desc": description,
        "icon": icon,
        "owner": owner
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(endpoint, json=payload, headers=headers)
    
    return response.json()

def list_all_knowledge_bases(owner_username):
    """
    List all knowledge bases for a specific owner.
    
    Parameters:
    - owner_username: Username of the owner
    
    Returns:
    - API response containing list of knowledge bases
    """
    endpoint = f"{BASE_URL}/list_all_kb/{owner_username}"
    
    response = requests.get(endpoint)
    
    return response.json()

def get_knowledge_base(owner_username, kb_name):
    """
    Get a specific knowledge base by owner and name.
    
    Parameters:
    - owner_username: Username of the owner
    - kb_name: Name of the knowledge base
    
    Returns:
    - API response containing knowledge base details
    """
    endpoint = f"{BASE_URL}/get_kb/{owner_username}/{kb_name}"
    
    response = requests.get(endpoint)
    
    return response.json()