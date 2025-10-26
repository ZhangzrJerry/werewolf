"""Test JSON recovery logic"""
import json
import re

# Sample truncated JSON from the error
truncated_json = """{
"per_player": {
"Alice": "As Seer, Alice checked Jack (good) on N1, a safe but low-impact choice. She failed to share her result before being eliminated, wasting her information.",
"Bob": "Bob initiated discussion well but made a critical error by voting for himself, which is never beneficial.",
"Frank": "Frank was a solid wolf who advocated against early pressure, a position that gained him town credibility. He helped steer"""

print("Original truncated JSON:")
print(truncated_json)
print("\n" + "="*60 + "\n")

# Test the recovery logic
text = truncated_json

# Try to fix truncated JSON by completing it
if not text.rstrip().endswith("}"):
    # Count opening and closing braces
    open_braces = text.count("{")
    close_braces = text.count("}")
    
    # If we have unclosed strings, try to close them
    if text.count('"') % 2 == 1:  # Odd number of quotes = unterminated string
        print("Detected unterminated string, adding closing quote")
        text = text + '"'
    
    # Close any unclosed braces
    while close_braces < open_braces:
        print(f"Adding closing brace ({close_braces}/{open_braces})")
        text = text + "}"
        close_braces += 1

print("After fixing:")
print(text)
print("\n" + "="*60 + "\n")

# Try to parse
try:
    data = json.loads(text)
    print("SUCCESS! Parsed JSON:")
    print(json.dumps(data, indent=2))
    print(f"\nRecovered {len(data.get('per_player', {}))} player reviews")
except json.JSONDecodeError as e:
    print(f"Still failed: {e}")
    print(f"Position: {e.pos}")
    
    # Try regex fallback
    print("\nTrying regex fallback...")
    per_player = {}
    player_pattern = r'"([^"]+)":\s*"((?:[^"\\]|\\.)*)"'
    
    per_player_start = text.find('"per_player"')
    if per_player_start != -1:
        section_start = text.find("{", per_player_start)
        if section_start != -1:
            section_end = len(text)
            per_player_text = text[section_start:section_end]
            matches = re.findall(player_pattern, per_player_text)
            per_player = {k: v for k, v in matches}
            
    print(f"Regex recovered {len(per_player)} players:")
    for name, review in per_player.items():
        print(f"  {name}: {review[:80]}...")
