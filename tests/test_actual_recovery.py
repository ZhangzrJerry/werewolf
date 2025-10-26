"""Test JSON recovery with actual failed response"""
import json
import re

# Read the actual failed response
with open('.training/debug_review_20251026_222631.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the JSON part
text = content.split('Full response:\n')[1]

print("Testing recovery with actual failed response...")
print(f"Original length: {len(text)} chars")
quote_count = text.count('"')
open_braces = text.count('{')
close_braces = text.count('}')
print(f"Quote count: {quote_count}")
print(f"Open braces: {open_braces}")
print(f"Close braces: {close_braces}")
print("\n" + "="*60 + "\n")

# Apply the recovery logic from learning_engine.py
per_player = {}
overall = ""
lessons = {}

# Try to fix truncated JSON by completing it
if not text.rstrip().endswith("}"):
    open_braces = text.count("{")
    close_braces = text.count("}")
    
    if text.count('"') % 2 == 1:  # Odd number of quotes = unterminated string
        print("Closing unterminated string")
        text = text + '"'
    
    while close_braces < open_braces:
        print(f"Adding closing brace ({close_braces}/{open_braces})")
        text = text + "}"
        close_braces += 1

# Now try to parse
try:
    data = json.loads(text)
    print("SUCCESS! Recovered complete JSON after fixing truncation")
    print(f"\nRecovered data:")
    print(f"  Per-player reviews: {len(data.get('per_player', {}))}")
    print(f"  Overall: {len(data.get('overall', ''))} chars")
    print(f"  Lessons: {len(data.get('lessons', {}))}")
    
    for name in data.get('per_player', {}):
        review = data['per_player'][name]
        print(f"    {name}: {review[:60]}...")
        
except json.JSONDecodeError as parse_error:
    print(f"Parse still failed: {parse_error}")
    print(f"Position: {parse_error.pos}")
    
    # Try regex fallback
    print("\nTrying regex fallback...")
    player_pattern = r'"([^"]+)":\s*"((?:[^"\\]|\\.)*)"'
    
    if '"per_player"' in text:
        per_player_start = text.find('"per_player"')
        if per_player_start != -1:
            section_start = text.find("{", per_player_start)
            if section_start != -1:
                section_end = len(text)
                for key in ['"overall"', '"lessons"']:
                    idx = text.find(key, section_start)
                    if idx != -1 and idx < section_end:
                        section_end = idx
                
                per_player_text = text[section_start:section_end]
                matches = re.findall(player_pattern, per_player_text)
                per_player = {k: v.replace('\\"', '"').replace('\\n', ' ') for k, v in matches}

    overall_match = re.search(r'"overall":\s*"((?:[^"\\]|\\.)*)"', text)
    if overall_match:
        overall = overall_match.group(1).replace('\\"', '"').replace('\\n', ' ')

    if per_player or overall:
        print(f"REGEX SUCCESS! Recovered {len(per_player)} players")
        for name, review in per_player.items():
            print(f"  {name}: {review[:60]}...")
    else:
        print("Regex recovery also failed")
