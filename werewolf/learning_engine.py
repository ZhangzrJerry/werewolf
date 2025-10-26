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
1) A concise per-player review (5-8 sentences each): decision quality, key mistakes, good moves, and concrete improvement tips.
2) An overall game summary explaining why the winner won and key turning points (6-10 sentences).
3) A short list of actionable strategy rules per role (Villager, Werewolf, Seer, Witch, Guardian, Hunter). Each rule must be a single imperative sentence (max 16 words), specific and non-obvious.

Winner: {winner}
Players and roles: {players}
Transcript:
---
{transcript}
---

CRITICAL INSTRUCTIONS:
- Return ONLY valid JSON
- NO markdown code blocks (no ```)
- NO explanatory text before or after
- Ensure ALL strings are properly quoted
- Escape special characters (quotes, newlines) properly
- Complete the entire JSON object

Expected format:
{{"per_player": {{"PlayerName": "review text"}}, "overall": "summary text", "lessons": {{"RoleName": ["rule1", "rule2"]}}}}

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
                # Look for first { and last }
                start_idx = text.find("{")
                end_idx = text.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    text = text[start_idx : end_idx + 1]

            # Additional cleanup: fix common JSON issues
            # Remove any trailing commas before closing braces
            import re

            text = re.sub(r",\s*}", "}", text)
            text = re.sub(r",\s*]", "]", text)

            # Parse JSON from extracted text
            data = json.loads(text)
        except json.JSONDecodeError as e:
            # Try to save partial JSON to file for debugging
            print(f"Warning: Failed to parse reviewer response: {e}")
            print(f"Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            if "text" in locals():
                print(f"Raw response (first 500 chars): {text[:500]}...")
                print(f"Raw response (last 200 chars): ...{text[-200:]}")
                # Save failed response for debugging
                try:
                    import datetime

                    debug_file = f".training/debug_review_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    import os

                    os.makedirs(".training", exist_ok=True)
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(f"Error: {e}\n\n")
                        f.write(f"Full response:\n{text}")
                    print(f"Saved failed response to {debug_file}")
                except Exception:
                    pass

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
You are a strategy critic for the Werewolf game. You will refine role-based rules.
- Remove duplicates and contradictions.
- Make each rule specific, imperative, and at most 16 words.
- Keep 5 or fewer rules per role, prioritized for impact.

Input lessons:
{json.dumps(lessons_by_role, indent=2)}

CRITICAL: Return ONLY valid JSON. No markdown, no code blocks, no explanation.
Format: {{"RoleName": ["rule1", "rule2", "rule3"]}}

Ensure all strings are properly quoted and escaped. Make sure the JSON is complete and valid.
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

            # Additional cleanup: fix common JSON issues
            import re

            text = re.sub(r",\s*}", "}", text)
            text = re.sub(r",\s*]", "]", text)

            # Parse JSON from extracted text
            data = json.loads(text)
            return {k: [str(x) for x in v] for k, v in data.items()}
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse critic response (JSON error): {e}")
            print(f"Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            if "text" in locals():
                print(f"Raw response (first 500 chars): {text[:500]}...")
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

    def save_rules_for_role(self, role_name: str, rules: List[str]) -> None:
        """Save strategy rules for a role, backing up the old version first"""
        path = self._file_for_role(role_name)

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

        # Save new strategy
        os.makedirs(self.root, exist_ok=True)
        data = {
            "rules": list(dict.fromkeys([r.strip() for r in rules if r.strip()])),
            "updated_at": datetime.datetime.now().isoformat(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

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
