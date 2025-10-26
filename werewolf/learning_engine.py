"""
Learning Engine: Post-game analysis and strategy optimization

- ReviewAgent: reads game transcript and produces per-player reviews and overall analysis
- CriticAgent: refines and critiques proposed strategy rules
- StrategyManager: persists per-role strategy rules and applies to agents
"""

from __future__ import annotations

import os
import json
import datetime
from typing import Dict, List, Any, Tuple

from .agents import WerewolfAgentBase
from .werewolf_game import Role

try:
    from agentscope.message import Msg  # type: ignore
except Exception:  # pragma: no cover

    class Msg:
        def __init__(self, name: str, content: str, role: str = "user") -> None:
            self.name = name
            self.content = content
            self.role = role


# Reuse model call helper from agents
from .agents import _run_model_sync


def _extract_and_fix_json(text: str) -> str:
    """Extract and attempt to fix malformed JSON from LLM response"""
    import re

    # Clean up markdown code blocks if present
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Try to find JSON object if text has extra content
    if not text.startswith("{"):
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1:
            text = text[start_idx : end_idx + 1]

    # Fix common JSON issues
    # Remove trailing commas before closing braces/brackets
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    # Try to fix unterminated strings by looking for unescaped quotes
    # This is a simple heuristic - won't catch all cases
    lines = text.split("\n")
    fixed_lines = []
    for line in lines:
        # If line contains an odd number of unescaped quotes, it's likely malformed
        # Count quotes that aren't escaped
        quote_count = len(re.findall(r'(?<!\\)"', line))
        if quote_count % 2 == 1 and not line.strip().endswith(","):
            # Try to close the string if it looks incomplete
            if ":" in line and '"' in line:
                # This is a crude fix - just escape internal quotes
                # Better: use proper JSON repair library
                pass
        fixed_lines.append(line)

    return text


class ReviewAgent:
    def __init__(self, model):
        self.model = model

    def analyze_transcript(
        self, transcript: str, roles: Dict[str, Role], winner: str
    ) -> Tuple[Dict[str, str], str, Dict[str, List[str]]]:
        """Return (per_player_reviews, overall_summary, lessons_by_role)"""
        players = ", ".join([f"{p}({roles[p].value})" for p in roles])

        # Truncate transcript if too long to avoid token limits
        max_transcript_length = 8000
        if len(transcript) > max_transcript_length:
            transcript = (
                transcript[:max_transcript_length]
                + "\n\n[... transcript truncated ...]"
            )

        prompt = f"""You are a Werewolf-game analyst. Read the full game transcript and produce:
1) A concise per-player review (3-4 sentences max, under 150 chars each): decision quality, key mistakes, and ONE improvement tip.
2) An overall game summary explaining why the winner won (4-5 sentences max, under 300 chars).
3) Strategy rules per role (Villager, Werewolf, Seer, Witch, Guardian, Hunter):
   - Extract 4-6 actionable strategies from this game for EACH role
   - Each rule must be specific, concrete, and under 15 words
   - Focus on: timing, communication, deception, information management, voting patterns
   - Include both successful tactics and lessons from mistakes

Winner: {winner}
Players and roles: {players}
Transcript:
---
{transcript}
---

CRITICAL JSON FORMATTING RULES - FOLLOW EXACTLY:
- Return ONLY valid JSON, nothing else
- NO markdown code blocks (no ```)
- ALL text must be on SINGLE LINES - replace newlines with spaces
- Use double quotes, escape internal quotes as \\"
- COMPLETE the entire JSON - don't truncate any entries
- Keep ALL reviews VERY brief (under 150 chars per player)
- Generate MORE strategy rules (4-6 per role) based on what happened in THIS game

Expected format (single line, no line breaks in strings):
{{"per_player": {{"PlayerName": "brief review"}}, "overall": "brief summary", "lessons": {{"RoleName": ["rule1", "rule2", "rule3", "rule4", "rule5"]}}}}

IMPORTANT: Make sure to close ALL quotes and braces. The response must end with }}
Start your response with {{ and end with }}
"""
        response = _run_model_sync(
            self.model, [Msg(name="reviewer", content=prompt, role="user")]
        )
        try:
            # Extract content from AgentScope response format
            content = getattr(response, "content", "")

            # Handle AgentScope's list[dict] format: [{'type': 'text', 'text': '...'}]
            if isinstance(content, list) and len(content) > 0:
                if isinstance(content[0], dict) and "text" in content[0]:
                    text = content[0]["text"]
                else:
                    text = str(content[0])
            else:
                text = str(content)

            # Use helper to extract and clean JSON
            text = _extract_and_fix_json(text)

            # Parse JSON from extracted text
            data = json.loads(text)
        except json.JSONDecodeError as e:
            # Save debug info and try to recover
            print(f"Warning: Failed to parse reviewer response: {e}")
            print(f"Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            if "text" in locals():
                print(f"Raw response (first 500 chars): {text[:500]}...")
                print(f"Raw response (last 200 chars): ...{text[-200:]}")
                # Save failed response for debugging
                try:
                    debug_file = f".training/debug_review_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    os.makedirs(".training", exist_ok=True)
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(f"Error: {e}\n\n")
                        f.write(f"Full response:\n{text}")
                    print(f"Saved failed response to {debug_file}")
                except Exception:
                    pass

            # Try one more time with aggressive regex extraction
            try:
                import re

                # Try to extract individual components using regex
                per_player = {}
                overall = ""
                lessons = {}

                # Try to fix truncated JSON by completing it
                # If the text doesn't end with }, try to close open structures
                if not text.rstrip().endswith("}"):
                    # Count opening and closing braces
                    open_braces = text.count("{")
                    close_braces = text.count("}")

                    # If we have unclosed strings, try to close them
                    # Find the last quote and see if it's escaped
                    if (
                        text.count('"') % 2 == 1
                    ):  # Odd number of quotes = unterminated string
                        text = text + '"'  # Close the string

                    # Close any unclosed braces
                    while close_braces < open_braces:
                        text = text + "}"
                        close_braces += 1

                # Now try to parse again
                try:
                    data = json.loads(text)
                    print("Recovered complete JSON after fixing truncation")
                except json.JSONDecodeError:
                    # If still failing, try regex extraction

                    # Extract per_player entries - handle both complete and incomplete entries
                    # First try complete entries (with closing quote)
                    player_pattern = r'"([^"]+)":\s*"((?:[^"\\]|\\.)*)"'

                    if '"per_player"' in text:
                        # Find the per_player section
                        per_player_start = text.find('"per_player"')
                        if per_player_start != -1:
                            # Extract everything after "per_player": {
                            section_start = text.find("{", per_player_start)
                            if section_start != -1:
                                # Find the end of per_player section (look for }, or next main key)
                                section_end = len(text)
                                for key in ['"overall"', '"lessons"']:
                                    idx = text.find(key, section_start)
                                    if idx != -1 and idx < section_end:
                                        section_end = idx

                                per_player_text = text[section_start:section_end]

                                # Extract all player entries
                                matches = re.findall(player_pattern, per_player_text)
                                per_player = {
                                    k: v.replace('\\"', '"').replace("\\n", " ")
                                    for k, v in matches
                                }

                    # Extract overall
                    overall_match = re.search(r'"overall":\s*"((?:[^"\\]|\\.)*)"', text)
                    if overall_match:
                        overall = (
                            overall_match.group(1)
                            .replace('\\"', '"')
                            .replace("\\n", " ")
                        )

                    # Extract lessons if present
                    if '"lessons"' in text:
                        lessons_start = text.find('"lessons"')
                        lessons_section = text[lessons_start:]
                        # Try to extract role-based lessons
                        role_pattern = r'"(Werewolf|Seer|Villager|Witch|Guardian|Hunter)":\s*\[((?:[^\]]*)?)\]'
                        role_matches = re.findall(role_pattern, lessons_section)
                        for role, rules_text in role_matches:
                            # Extract individual rules
                            rules = re.findall(r'"([^"]+)"', rules_text)
                            lessons[role] = rules

                    # If we got something useful, use it
                    if per_player or overall:
                        print(
                            f"Recovered partial data using regex fallback ({len(per_player)} players)"
                        )
                        data = {
                            "per_player": per_player,
                            "overall": overall,
                            "lessons": lessons,
                        }
                    else:
                        raise ValueError("Regex recovery failed")

            except Exception as recovery_error:
                print(f"Recovery attempt failed: {recovery_error}")
                # Fallback minimal structure
                data = {
                    "per_player": {},
                    "overall": "Failed to parse review response - please check debug file",
                    "lessons": {},
                }
        except Exception as e:
            print(f"Warning: Unexpected error in reviewer: {e}")
            data = {
                "per_player": {},
                "overall": "Error during review",
                "lessons": {},
            }
        per_player = {k: str(v) for k, v in data.get("per_player", {}).items()}
        lessons = {k: [str(x) for x in v] for k, v in data.get("lessons", {}).items()}
        overall = str(data.get("overall", ""))
        return per_player, overall, lessons


class CriticAgent:
    def __init__(self, model):
        self.model = model

    def refine_lessons(
        self, lessons_by_role: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        prompt = f"""
You are a strategy critic for the Werewolf game. Refine and consolidate role-based rules.

Your tasks:
1. MERGE similar or overlapping rules into comprehensive ones
2. Remove exact duplicates and contradictions
3. Keep rules specific, imperative, and actionable (max 18 words each)
4. Preserve 6-10 high-impact rules per role (prioritize quality and coverage)
5. Organize rules by theme: early-game, mid-game, communication, deception, voting

Input lessons:
{json.dumps(lessons_by_role, indent=2)}

CRITICAL JSON FORMATTING RULES:
- Return ONLY valid JSON, nothing else
- NO markdown code blocks (no ```)
- Keep all text on SINGLE LINES - replace any newlines with spaces
- Use double quotes for strings
- Escape internal quotes as \\"
- Complete the entire JSON object

Format: {{"RoleName": ["rule1", "rule2", "rule3", "rule4", "rule5", "rule6"]}}

Examples of GOOD merging:
Input: ["Claim Seer early if you verified someone", "Seers should reveal after first good check"]
Output: ["Claim Seer immediately after verifying a good player to build trust circle"]

Input: ["Vote with the majority", "Follow consensus on votes"]
Output: ["Analyze voting patterns rather than blindly following consensus"]

Generate merged, high-quality rules (6-10 per role).
"""
        response = _run_model_sync(
            self.model, [Msg(name="critic", content=prompt, role="user")]
        )
        try:
            # Extract content from AgentScope response format
            content = getattr(response, "content", "")

            # Handle AgentScope's list[dict] format: [{'type': 'text', 'text': '...'}]
            if isinstance(content, list) and len(content) > 0:
                if isinstance(content[0], dict) and "text" in content[0]:
                    text = content[0]["text"]
                else:
                    text = str(content[0])
            else:
                text = str(content)

            # Use helper to extract and clean JSON
            text = _extract_and_fix_json(text)

            # Parse JSON from extracted text
            data = json.loads(text)
            return {k: [str(x) for x in v] for k, v in data.items()}
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse critic response (JSON error): {e}")
            print(f"Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            if "text" in locals():
                print(f"Raw response (first 500 chars): {text[:500]}...")
                # Save failed response for debugging
                try:
                    debug_file = f".training/debug_critic_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    os.makedirs(".training", exist_ok=True)
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(f"Error: {e}\n\n")
                        f.write(f"Full response:\n{text}")
                    print(f"Saved failed response to {debug_file}")
                except Exception:
                    pass
            # Return original lessons if parsing fails
            return lessons_by_role
        except Exception as e:
            print(f"Warning: Failed to parse critic response: {e}")
            return lessons_by_role


class StrategyManager:
    def __init__(self, root: str = None) -> None:
        self.root = root or os.path.join(os.getcwd(), ".training", "strategies")
        self.backup_root = os.path.join(self.root, "backups")
        os.makedirs(self.root, exist_ok=True)
        os.makedirs(self.backup_root, exist_ok=True)

    def _file_for_role(self, role_name: str) -> str:
        fname = role_name.lower() + ".json"
        return os.path.join(self.root, fname)

    def _backup_file_for_role(self, role_name: str, timestamp: str) -> str:
        """Generate backup filename with timestamp"""
        fname = f"{role_name.lower()}_{timestamp}.json"
        return os.path.join(self.backup_root, fname)

    def load_rules_for_role(self, role_name: str) -> List[str]:
        path = self._file_for_role(role_name)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [r for r in data.get("rules", []) if isinstance(r, str)]
        except Exception:
            return []

    def save_rules_for_role(
        self, role_name: str, rules: List[str], merge_with_existing: bool = True
    ) -> None:
        """Save strategy rules for a role, optionally merging with existing rules

        Args:
            role_name: The role to save rules for
            rules: New rules to save
            merge_with_existing: If True, merge with existing rules and deduplicate
        """
        path = self._file_for_role(role_name)

        # Load existing rules if merging
        existing_rules = []
        if merge_with_existing and os.path.exists(path):
            existing_rules = self.load_rules_for_role(role_name)

        # Backup existing file before overwriting
        if os.path.exists(path):
            # Use microseconds to ensure unique backup filenames
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_path = self._backup_file_for_role(role_name, timestamp)
            try:
                import shutil

                shutil.copy2(path, backup_path)
            except Exception as e:
                print(f"Warning: Failed to backup {role_name} strategy: {e}")

        # Merge and deduplicate rules
        if merge_with_existing and existing_rules:
            # Combine old and new rules
            all_rules = existing_rules + rules
            # Simple deduplication: remove exact duplicates (case-insensitive)
            seen = set()
            unique_rules = []
            for rule in all_rules:
                rule_lower = rule.lower().strip()
                if rule_lower and rule_lower not in seen:
                    seen.add(rule_lower)
                    unique_rules.append(rule.strip())
            # Keep most recent rules (limit to prevent explosion)
            final_rules = unique_rules[-15:]  # Keep up to 15 rules max
        else:
            # Just use new rules
            final_rules = [r.strip() for r in rules if r.strip()]

        # Save new strategy
        os.makedirs(self.root, exist_ok=True)
        data = {
            "rules": final_rules,
            "updated_at": datetime.datetime.now().isoformat(),
            "total_updates": len(existing_rules) if existing_rules else 0,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(
            f"Saved {len(final_rules)} rules for {role_name} (merged: {merge_with_existing})"
        )

    def apply_to_agents(
        self, agents: Dict[str, WerewolfAgentBase], roles: Dict[str, Role]
    ):
        for name, agent in agents.items():
            role_name = roles[name].value
            rules = self.load_rules_for_role(role_name)
            if rules:
                agent.set_strategy_rules(rules)


def run_learning_pipeline(
    log_file: str, agents: Dict[str, WerewolfAgentBase], roles: Dict[str, Role], model
) -> str:
    """Run end-to-end learning pipeline. Returns review directory path."""
    # Read transcript
    with open(log_file, "r", encoding="utf-8") as f:
        transcript = f.read()

    # Winner detection (last lines contain winner)
    winner = ""
    for line in transcript.splitlines()[::-1]:
        if line.strip().startswith("[WINNER]"):
            winner = line.split("]", 1)[1].strip().lower()
            break

    # Prepare output dir
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    review_dir = os.path.join(os.getcwd(), ".training", "reviews", timestamp)
    os.makedirs(review_dir, exist_ok=True)

    reviewer = ReviewAgent(model)
    per_player, overall, lessons = reviewer.analyze_transcript(
        transcript, roles, winner
    )

    critic = CriticAgent(model)
    refined_lessons = critic.refine_lessons(lessons)

    # Save reports
    for player, text in per_player.items():
        with open(
            os.path.join(review_dir, f"{player}_review.txt"), "w", encoding="utf-8"
        ) as f:
            f.write(text)

    # Save overall as plain text
    with open(os.path.join(review_dir, "overall.txt"), "w", encoding="utf-8") as f:
        f.write(overall)

    # Save lessons as proper JSON
    with open(os.path.join(review_dir, "lessons.json"), "w", encoding="utf-8") as f:
        json.dump(refined_lessons, f, ensure_ascii=False, indent=2)

    # Also save raw data for debugging
    with open(
        os.path.join(review_dir, "full_analysis.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "per_player": per_player,
                "overall": overall,
                "lessons": refined_lessons,
                "winner": winner,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # Persist strategies by role
    sm = StrategyManager()
    for role_name, rules in refined_lessons.items():
        sm.save_rules_for_role(role_name, rules)

    # Apply to current agents in-memory for next games in same process
    sm.apply_to_agents(agents, roles)

    return review_dir
