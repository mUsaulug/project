
import os
import sys
import json
import time

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import llm_client
from app.core.constants import CATEGORY_VALUES

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic_dataset.json")

PERSONAS = [
    {
        "name": "Angry Customer",
        "desc": "You are furious. Use uppercase words, multiple exclamation marks, and threats to leave the bank. Mention huge inconvenience.",
    },
    {
        "name": "Gen-Z",
        "desc": "You are young. Use lowercase, slang, abbreviations (tşk, mrb, naber), emojis, and short sentences.",
    },
    {
        "name": "Elderly / Non-Tech",
        "desc": "You are old and confused. Use very formal or very simple language. Complain about technology being hard. Ask for help politely.",
    },
    {
        "name": "Anxious User",
        "desc": "You are panicked. Use words like 'acil', 'lütfen', 'korkuyorum', 'dolandırıldım mı?'.",
    }
]

def generate_samples():
    new_records = []
    
    print(f"Generating synthetic data for {len(CATEGORY_VALUES)} categories x {len(PERSONAS)} personas...")

    for category in CATEGORY_VALUES:
        if category == "TECHNICAL_ISSUE": continue # Skip if not in main list
        
        for persona in PERSONAS:
            print(f"  -> Generating for {category} as {persona['name']}...")
            
            prompt = f"""
            Roleplay: {persona['desc']}
            Task: Write 3 distinct banking complaint/request sentences related to the category: '{category}'.
            Language: Turkish (Natural, with typos or slang if appropriate for persona).
            Format: Return ONLY a raw JSON list of strings. Example: ["sentence 1", "sentence 2", "sentence 3"]
            """
            
            try:
                # We use the raw client or generate_response. 
                # Since generate_response expects specific inputs, let's use the openai client directly if possible
                # Or repurpose generate_response. Ideally llm_client should expose a raw generic method.
                # Inspecting llm_client, it likely has a client.chat.completions.create logic.
                
                # HACK: Using a temporary internal access or creating a new method.
                # For this script, we'll instantiate OpenAI directly to avoid modifying llm_client too much 
                # or assume llm_client wrapper has a 'client' attribute we can use.
                
                from openai import OpenAI
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo", # or gpt-4o if available
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8
                )
                
                content = response.choices[0].message.content.strip()
                # clean potential markdown code blocks
                if content.startswith("```json"):
                    content = content[7:-3]
                
                sentences = json.loads(content)
                
                for s in sentences:
                    new_records.append({
                        "text": s,
                        "category": category,
                        "urgency": "RED" if "FRAUD" in category or "ACCESS" in category else "GREEN", # Simple heuristic
                        "source": f"synthetic_{persona['name']}"
                    })
                    
            except Exception as e:
                print(f"    Error: {e}")
                time.sleep(1)

    # Save
    print(f"Generated {len(new_records)} new records.")
    
    # Save to file (append or overwrite)
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        combined = existing + new_records
    else:
        combined = new_records
        
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
        
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_samples()
