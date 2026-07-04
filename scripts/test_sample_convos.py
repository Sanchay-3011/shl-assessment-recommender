import os
import re
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def parse_markdown_conversation(filepath: str):
    """
    Parses a C*.md file and returns a list of dictionaries,
    each containing the user's message for that turn.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by turns
    turns = re.split(r'### Turn \d+', content)
    
    parsed_turns = []
    
    for turn in turns[1:]: # Skip the first element which is just "## Conversation"
        # Extract user message
        user_match = re.search(r'\*\*User\*\*\n+\> (.*?)\n+\*\*Agent\*\*', turn, re.DOTALL)
        if user_match:
            user_msg = user_match.group(1).strip()
            parsed_turns.append({"user": user_msg})
            
    return parsed_turns

def run_tests():
    data_dir = "data/sample_convo"
    files = [f for f in os.listdir(data_dir) if f.startswith("C") and f.endswith(".md")]
    
    for file in files:
        filepath = os.path.join(data_dir, file)
        print(f"\n{'='*50}\nTesting {file}\n{'='*50}")
        
        turns = parse_markdown_conversation(filepath)
        messages = []
        
        for i, turn in enumerate(turns):
            user_msg = turn["user"]
            messages.append({"role": "user", "content": user_msg})
            
            print(f"\n--- Turn {i+1} ---")
            print(f"User: {user_msg}")
            
            response = client.post("/chat", json={"messages": messages})
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}")
                print(response.text)
                break
                
            data = response.json()
            agent_reply = data.get("reply", "")
            recommendations = data.get("recommendations", [])
            end_conv = data.get("end_of_conversation", False)
            
            print(f"Agent: {agent_reply}")
            print(f"Recommendations: {len(recommendations)} items")
            print(f"End of conversation: {end_conv}")
            
            messages.append({"role": "assistant", "content": agent_reply})
            
            if end_conv:
                print("Conversation ended naturally.")
                break

if __name__ == "__main__":
    run_tests()
