import json
import os
import re

# Priority order for test types
ORDER = ['P', 'A', 'B', 'C', 'D', 'E', 'K', 'S']

KEY_TO_CODE = {
    "Personality & Behavior": "P",
    "Ability & Aptitude": "A",
    "Biodata & Situational Judgment": "B",
    "Competencies": "C",
    "Development & 360": "D",
    "Assessment Exercises": "E",
    "Knowledge & Skills": "K",
    "Simulations": "S"
}

def clean_catalog(input_path: str, output_path: str):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input catalog not found at {input_path}")
        
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Parse with strict=False to handle control characters
    raw_data = json.loads(text, strict=False)
    cleaned_data = []

    for item in raw_data:
        name = item.get("name", "")
        # Filter out pre-packaged Job Solutions and bundles
        if "solution" in name.lower():
            continue
        
        link = item.get("link", "")
        description = item.get("description", "")
        keys = item.get("keys", [])
        duration = item.get("duration", "")
        job_levels = item.get("job_levels", [])
        languages = item.get("languages", [])
        
        # Calculate test_type
        codes = [KEY_TO_CODE[k] for k in keys if k in KEY_TO_CODE]
        # De-duplicate and sort according to ORDER priority
        sorted_codes = sorted(list(set(codes)), key=lambda x: ORDER.index(x) if x in ORDER else 99)
        test_type = ",".join(sorted_codes)
        
        # If no keys or codes mapped, default to "K" (Knowledge)
        if not test_type:
            test_type = "K"
            
        cleaned_item = {
            "entity_id": item.get("entity_id", ""),
            "name": name,
            "url": link,
            "description": description,
            "test_type": test_type,
            "duration": duration,
            "keys": keys,
            "job_levels": job_levels,
            "languages": languages
        }
        cleaned_data.append(cleaned_item)
        
    # Ensure resource directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        
    print(f"Cleaned catalog created at {output_path} with {len(cleaned_data)} items (filtered from {len(raw_data)}).")

if __name__ == "__main__":
    # If run directly, clean the catalog
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_file = os.path.join(base_dir, "shl_product_catalog.json")
    output_file = os.path.join(base_dir, "app", "resources", "cleaned_catalog.json")
    clean_catalog(input_file, output_file)
