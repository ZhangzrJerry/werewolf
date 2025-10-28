"""
AgentScope-based intelligent agents for Werewolf game

This module is resilient to missing AgentScope at import time to allow
tests to run in environments without the agentscope package. When
AgentScope isn't available, lightweight stubs are used which are
adequate for unit tests that don't actually invoke models.
"""

from typing import Dict, List, Any, Optional
import asyncio

# Optional AgentScope import with graceful fallback for environments without it
try:
    from agentscope.agent import AgentBase  # type: ignore
    from agentscope.message import Msg  # type: ignore
    from agentscope.model import (  # type: ignore
        OpenAIChatModel,
        DashScopeChatModel,
        OllamaChatModel,
    )

    _AGENTSCOPE_AVAILABLE = True
except Exception:  # pragma: no cover
    _AGENTSCOPE_AVAILABLE = False

    class AgentBase:  # minimal stub
        def __init__(self, *args, **kwargs) -> None:
            pass

        def model(self, *args, **kwargs):
            class _Resp:
                content = ""

            return _Resp()

    class OpenAIChatModel:  # stub
        pass

    class DashScopeChatModel:  # stub
        pass

    class OllamaChatModel:  # stub
        pass

    class Msg:
        def __init__(self, name: str, content: str, role: str = "user") -> None:
            self.name = name
            self.content = content
            self.role = role


from .werewolf_game import Role, GamePhase


def _extract_text_content(response):
    """Extract text content from AgentScope model response

    Args:
        response: ModelResponse object from AgentScope model

    Returns:
        str: Extracted text content
    """
    content = response.content
    if isinstance(content, list):
        # Content blocks - extract text
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                # Handle dict format like {'type': 'text', 'text': '...'}
                text_parts.append(block["text"])
            elif hasattr(block, "text"):
                text_parts.append(block.text)
            else:
                text_parts.append(str(block))
        return " ".join(text_parts)
    elif isinstance(content, str):
        return content
    else:
        return str(content)


def _run_model_sync(model, msg_list, max_retries: int = 3):
    """Synchronous wrapper for async model calls with retry logic

    Args:
        model: The AgentScope model instance
        msg_list: List of Msg objects to send to the model
        max_retries: Maximum number of retry attempts for network errors
    """
    import time

    # Retry logic for handling network errors
    last_error = None
    for attempt in range(max_retries):
        try:
            # Get or create event loop
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in current thread, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            # Convert Msg objects to dict format expected by model
            # AgentScope 1.0 models expect list of dicts with 'role' and 'content'
            messages = []
            for msg in msg_list:
                if hasattr(msg, "to_dict"):
                    msg_dict = msg.to_dict()
                    messages.append(
                        {"role": msg_dict["role"], "content": msg_dict["content"]}
                    )
                else:
                    # Fallback for dict input
                    messages.append(msg)

            # Run the async model call synchronously
            # Note: stream setting should be in model's generate_kwargs config
            import inspect

            response = loop.run_until_complete(model(messages))

            # Check if response is async generator (stream=True case)
            if inspect.isasyncgen(response):
                # Consume the generator to get the final response
                async def consume_stream():
                    final_response = None
                    async for chunk in response:
                        final_response = chunk
                    return final_response

                response = loop.run_until_complete(consume_stream())

            return response

        except Exception as e:
            last_error = e
            error_msg = str(e).lower()

            # Check if it's a retryable network error
            is_network_error = any(
                keyword in error_msg
                for keyword in [
                    "peer closed connection",
                    "incomplete chunked read",
                    "connection reset",
                    "timeout",
                    "connection error",
                    "remote protocol error",
                ]
            )

            if is_network_error and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                print(f"Network error (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                # Non-retryable error or max retries reached
                raise

    # If we get here, all retries failed
    raise last_error


class WerewolfAgentBase(AgentBase):
    """Base class for all Werewolf game agents"""

    def __init__(
        self,
        name: str,
        role: Role,
        model_config_name: str,
        sys_prompt: str = None,
        **kwargs,
    ):
        # Create model directly from config
        self.name = name
        self.role = role
        self.is_alive = True
        self.known_roles: Dict[str, Role] = {name: role}
        self.memory_history: List[Dict[str, Any]] = []
        self.sys_prompt = sys_prompt or self._get_default_sys_prompt()
        # Strategy rules injected by Learning Engine to guide behavior per role
        self.strategy_rules: List[str] = []

        # Initialize model - create model instance directly
        self.model_config_name = model_config_name
        from werewolf.config import MODEL_CONFIGS

        model_config = next(
            (c for c in MODEL_CONFIGS if c["config_name"] == model_config_name), None
        )
        if model_config:
            model_type = model_config.get("model_type", "openai_chat")

            # Prepare parameters for different model types
            if model_type == "openai_chat":
                # OpenAI-compatible models (OpenAI, DeepSeek, ModelScope)
                params = {
                    "model_name": model_config["model_name"],
                    "api_key": model_config.get("api_key"),
                    "organization": model_config.get("organization"),
                    "generate_kwargs": model_config.get("generate_args", {}),
                }
                # base_url goes into client_args for OpenAI models
                if "base_url" in model_config:
                    params["client_args"] = {"base_url": model_config["base_url"]}
                try:
                    self.model = OpenAIChatModel(
                        **{k: v for k, v in params.items() if v is not None}
                    )
                except Exception as e:
                    print(f"Warning: Failed to initialize OpenAI model: {e}")
                    self.model = lambda msg: type("obj", (object,), {"content": ""})()

            elif model_type == "dashscope_chat":
                params = {
                    "model_name": model_config["model_name"],
                    "api_key": model_config.get("api_key"),
                    "generate_kwargs": model_config.get("generate_args", {}),
                }
                try:
                    self.model = DashScopeChatModel(
                        **{k: v for k, v in params.items() if v is not None}
                    )
                except Exception as e:
                    print(f"Warning: Failed to initialize DashScope model: {e}")
                    self.model = lambda msg: type("obj", (object,), {"content": ""})()

            elif model_type == "ollama_chat":
                params = {
                    "model_name": model_config["model_name"],
                    "host": model_config.get("host", "http://localhost:11434"),
                    "generate_kwargs": model_config.get("generate_args", {}),
                }
                try:
                    self.model = OllamaChatModel(
                        **{k: v for k, v in params.items() if v is not None}
                    )
                except Exception as e:
                    print(f"Warning: Failed to initialize Ollama model: {e}")
                    self.model = lambda msg: type("obj", (object,), {"content": ""})()
            else:
                # Fallback
                self.model = lambda msg: type("obj", (object,), {"content": ""})()
        else:
            # No config found - create stub
            self.model = lambda msg: type("obj", (object,), {"content": ""})()

    # Strategy API
    def set_strategy_rules(self, rules: List[str]):
        """Replace current strategy rules with new ones"""
        self.strategy_rules = [r.strip() for r in rules if r and r.strip()]

    def add_strategy_rules(self, rules: List[str]):
        """Append additional strategy rules, de-duplicated"""
        current = set(self.strategy_rules)
        for r in rules:
            if r and r.strip() and r.strip() not in current:
                self.strategy_rules.append(r.strip())
                current.add(r.strip())

    def _format_strategy_rules(self) -> str:
        if not self.strategy_rules:
            return "(none)"
        return "\n".join([f"- {r}" for r in self.strategy_rules])

    def _get_default_sys_prompt(self) -> str:
        """Get default system prompt based on role"""
        return f"""You are playing the Werewolf game as a {self.role.value}.
Your goal is to help your team win through strategic thinking and communication.
Always think carefully about your actions and their consequences."""

    def update_game_state(self, game_state: Dict[str, Any]):
        """Update agent's knowledge of game state"""
        self.memory_history.append(
            {
                "type": "game_state_update",
                "state": game_state,
                "day": game_state.get("day_count", 0),
            }
        )

    def receive_information(self, info: Dict[str, Any]):
        """Receive and store information (e.g., seer check results)"""
        self.memory_history.append({"type": "information", "content": info})

    def mark_dead(self):
        """Mark this agent as dead"""
        self.is_alive = False

    def last_words(self, context: str, cause_of_death: str) -> str:
        """Provide last words before death

        Args:
            context: Current game context
            cause_of_death: How the player died (werewolf_kill, voted_out, witch_poison)
        """
        prompt = f"""You are about to die in the Werewolf game.
        
Your Role: {self.role.value}
Cause of Death: {cause_of_death}

Game Context:
{context}

This is your last chance to speak. What are your final words?
Consider:
1. Share any important information you actually know
2. Express your suspicions based on discussions
3. Guide your allies (if you're on the good side)
4. Reveal your role only if it helps your team

Your last words (keep it brief, 2-3 sentences):"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return _extract_text_content(response)


class VillagerAgent(WerewolfAgentBase):
    """Villager agent - good side, no special abilities"""

    def _get_default_sys_prompt(self) -> str:
        return """You are a VILLAGER in the Werewolf game.

Your Role:
- You are on the good side
- You have no special abilities
- Your goal is to identify and eliminate werewolves through voting

Strategy:
1. Listen carefully to all discussions
2. Look for inconsistencies in other players' statements
3. Analyze voting patterns to identify suspicious behavior
4. Defend yourself if accused, but don't seem too defensive
5. Build trust with other villagers
6. Vote to eliminate the most suspicious players

Communication Style:
- Be logical and analytical
- Ask probing questions
- Share your observations without revealing too much
- Collaborate with others to find werewolves"""

    def discuss(self, context: str, discussion_history: List[Msg]) -> str:
        """Participate in day discussion"""
        prompt = f"""Current game context:
{context}

Recent discussion:
{self._format_discussion(discussion_history)}

Strategy guidelines for your role:
{self._format_strategy_rules()}

As a villager, speak naturally about what you think. Talk like a real person in a conversation, not like you're writing a report. Share your thoughts, suspicions, and questions in 2-4 sentences.

IMPORTANT: Just provide your statement directly. Do NOT start with your name.

Your statement:"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return _extract_text_content(response)

    def vote(self, context: str, alive_players: List[str]) -> str:
        """Vote for a player to eliminate"""
        prompt = f"""Current game context:
{context}

Alive players: {', '.join(alive_players)}

Strategy guidelines for your role:
{self._format_strategy_rules()}

Based on all discussions and your observations, who should be voted out?
Provide your vote and brief reasoning.

Format: VOTE: [player_name]
Reasoning: [your reasoning]"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return self._extract_vote(_extract_text_content(response), alive_players)

    def _format_discussion(self, messages: List[Msg]) -> str:
        """Format discussion messages for prompt"""
        if not messages:
            return "No discussion yet."
        return "\n".join([f"{msg.name}: {msg.content}" for msg in messages[-10:]])

    def _extract_vote(self, response: str, valid_players: List[str]) -> str:
        """Extract vote from agent response"""
        response_upper = response.upper()
        for player in valid_players:
            if player.upper() in response_upper:
                return player
        return valid_players[0] if valid_players else ""


class WerewolfAgent(WerewolfAgentBase):
    """Werewolf agent - evil side, can kill at night"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kill_history: List[Dict[str, str]] = []  # Track who was killed each night

    def _get_default_sys_prompt(self) -> str:
        return """You are a WEREWOLF in the Werewolf game.

Your Role:
- You are on the werewolf team
- You know who the other werewolves are
- At night, you coordinate with other werewolves to kill a villager
- During the day, you must blend in and avoid detection

Strategy:
1. Pretend to be a villager during day discussions
2. Coordinate with fellow werewolves at night
3. Avoid being too aggressive or too passive
4. Create confusion and misdirection
5. Protect fellow werewolves without being obvious
6. Vote strategically to eliminate strong villagers

Deception Tactics:
- Claim to be a villager if questioned
- Occasionally agree with villagers to build trust
- Subtly shift suspicion to actual villagers
- Avoid defending werewolf teammates too obviously
- Create believable alibis and reasoning

CRITICAL: Never reveal you are a werewolf during day discussions!"""

    def discuss(self, context: str, discussion_history: List[Msg]) -> str:
        """Participate in day discussion while hiding identity"""
        prompt = f"""Current game context:
{context}

Recent discussion:
{self._format_discussion(discussion_history)}

Strategy guidelines for your role:
{self._format_strategy_rules()}

You're a werewolf pretending to be an innocent villager. Speak naturally like you're in a real conversation - share your thoughts and suspicions in 2-4 sentences, but stay in character and don't reveal you're a werewolf.

IMPORTANT: Just provide your statement directly. Do NOT start with your name.

Your statement:"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return _extract_text_content(response)

    def night_action(
        self, context: str, targets: List[str], team_members: List[str]
    ) -> str:
        """Choose target to kill at night"""
        prompt = f"""Night Phase - Werewolf Team Discussion

Your werewolf team: {', '.join(team_members)}
Possible targets: {', '.join(targets)}

Context:
{context}

Strategy guidelines for your role:
{self._format_strategy_rules()}

Who should the werewolf team kill tonight? Consider:
1. Who is the biggest threat to werewolves?
2. Who is leading the villagers?
3. Who might have special roles (seer, witch)?
4. Avoid patterns that reveal your strategy

Your choice: """

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        content = _extract_text_content(response)
        return self._extract_vote(content, targets)

    def _format_discussion(self, messages: List[Msg]) -> str:
        if not messages:
            return "No discussion yet."
        return "\n".join([f"{msg.name}: {msg.content}" for msg in messages[-10:]])

    def _format_kill_history(self) -> str:
        """Format werewolf kill history for prompts"""
        if not self.kill_history:
            return "No kills recorded yet."
        return "\n".join(
            [
                f"Night {i+1}: Targeted {k['target']}"
                + (f" (Result: {k['result']})" if "result" in k else "")
                for i, k in enumerate(self.kill_history)
            ]
        )

    def _extract_vote(self, response: str, valid_players: List[str]) -> str:
        response_upper = response.upper()
        for player in valid_players:
            if player.upper() in response_upper:
                return player
        return valid_players[0] if valid_players else ""

    def record_kill_result(self, target: str, result: str = "unknown"):
        """Record the result of a kill attempt"""
        self.kill_history.append({"target": target, "result": result})

    def vote(self, context: str, alive_players: List[str]) -> str:
        """Vote for a player to eliminate (as werewolf pretending to be villager)"""
        prompt = f"""Current game context:
{context}

Alive players: {', '.join(alive_players)}

Strategy guidelines for your role:
{self._format_strategy_rules()}

As a werewolf PRETENDING to be a villager, who should you vote for?
Consider:
1. Don't vote for your werewolf allies
2. Vote for threats or active villagers
3. Blend in with other voters
4. Don't draw suspicion to yourself

Format: VOTE: [player_name]
Reasoning: [your fake reasoning]"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        # Filter out werewolf teammates from valid vote options
        non_werewolf_players = [
            p for p in alive_players if self.known_roles.get(p) != Role.WEREWOLF
        ]
        if not non_werewolf_players:
            non_werewolf_players = alive_players  # Fallback
        return self._extract_vote(_extract_text_content(response), non_werewolf_players)


class SeerAgent(WerewolfAgentBase):
    """Seer agent - can check one player's role each night"""

    def _get_default_sys_prompt(self) -> str:
        return """You are the SEER in the Werewolf game.

Your Role:
- You are on the good side
- Each night, you can check one player's true identity
- You know who the werewolves are (after checking them)
- Your goal is to use this information to help eliminate werewolves

Strategy:
1. Check suspicious players at night
2. Share information carefully to avoid being killed
3. Don't reveal your role too early (werewolves will target you)
4. Build trust with confirmed villagers
5. Guide discussions subtly without being obvious
6. Consider revealing your role late game with proof

Information Sharing:
- Be strategic about when to reveal findings
- Don't reveal you're the seer until necessary
- Use indirect language to guide suspicion
- Confirm villagers to build a coalition
- Reveal werewolves at the right moment"""

    def night_action(self, context: str, targets: List[str]) -> str:
        """Choose player to check at night"""
        # Filter out players already checked (excluding self)
        checked_players = set(self.known_roles.keys()) - {self.name}
        unchecked_targets = [t for t in targets if t not in checked_players]

        # If all players have been checked, allow re-checking (fallback)
        available_targets = unchecked_targets if unchecked_targets else targets

        prompt = f"""Night Phase - Seer's Check

Available targets: {', '.join(available_targets)}
{f"(Note: You've already checked: {', '.join(checked_players)})" if checked_players else ""}

Context:
{context}

Players you've already checked:
{self._format_known_roles()}

Strategy guidelines for your role:
{self._format_strategy_rules()}

Who should you check tonight? Consider:
1. Most suspicious players from discussions
2. Players you haven't checked yet
3. Key players in leadership positions

Your choice:"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return self._extract_choice(_extract_text_content(response), available_targets)

    def discuss(self, context: str, discussion_history: List[Msg]) -> str:
        """Participate in discussion with knowledge of roles"""
        known_wolves = [
            p
            for p, r in self.known_roles.items()
            if r == Role.WEREWOLF and p != self.name
        ]

        prompt = f"""Current game context:
{context}

Recent discussion:
{self._format_discussion(discussion_history)}

Your knowledge as Seer:
{self._format_known_roles()}

Strategy guidelines for your role:
{self._format_strategy_rules()}

You're the seer, but don't reveal it too obviously. Speak naturally like in a conversation (2-4 sentences). Guide others toward suspecting werewolves without being too direct.
{f'You know these are werewolves: {", ".join(known_wolves)}' if known_wolves else ''}

IMPORTANT: Just provide your statement directly. Do NOT start with your name.

Your statement:"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return _extract_text_content(response)

    def _format_known_roles(self) -> str:
        if len(self.known_roles) <= 1:
            return "No players checked yet."
        return "\n".join(
            [
                f"- {player}: {role.value}"
                for player, role in self.known_roles.items()
                if player != self.name
            ]
        )

    def _format_discussion(self, messages: List[Msg]) -> str:
        if not messages:
            return "No discussion yet."
        return "\n".join([f"{msg.name}: {msg.content}" for msg in messages[-10:]])

    def _extract_choice(self, response: str, valid_players: List[str]) -> str:
        response_upper = response.upper()
        for player in valid_players:
            if player.upper() in response_upper:
                return player
        return valid_players[0] if valid_players else ""

    def vote(self, context: str, alive_players: List[str]) -> str:
        """Vote for a player to eliminate (using seer knowledge)"""
        known_wolves = [
            p
            for p, r in self.known_roles.items()
            if r == Role.WEREWOLF and p in alive_players
        ]

        prompt = f"""Current game context:
{context}

Alive players: {', '.join(alive_players)}

Your knowledge as Seer:
{self._format_known_roles()}

Strategy guidelines for your role:
{self._format_strategy_rules()}

As the seer, who should you vote for?
{'Priority: Vote for known werewolves: ' + ', '.join(known_wolves) if known_wolves else 'Vote based on discussion and suspicion.'}

Format: VOTE: [player_name]
Reasoning: [your reasoning - be careful not to reveal too much seer knowledge]"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return self._extract_vote(_extract_text_content(response), alive_players)

    def _extract_vote(self, response: str, valid_players: List[str]) -> str:
        response_upper = response.upper()
        for player in valid_players:
            if player.upper() in response_upper:
                return player
        return valid_players[0] if valid_players else ""


class WitchAgent(WerewolfAgentBase):
    """Witch agent - has one antidote and one poison"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.antidote_used = False
        self.poison_used = False
        self.night_victims: List[Dict[str, Any]] = (
            []
        )  # Track who was attacked each night
        self.saved_player: str = None  # Who was saved with antidote
        self.poisoned_player: str = None  # Who was poisoned

    def _get_default_sys_prompt(self) -> str:
        return """You are the WITCH in the Werewolf game.

Your Role:
- You are on the good side
- You have one antidote (save the werewolf victim once)
- You have one poison (kill any player once)
- You learn who the werewolves targeted each night

Strategy:
1. Save the antidote for critical players or yourself
2. Use poison on confirmed werewolves
3. Don't use both abilities too early
4. Keep your role secret to avoid being targeted
5. Share information about night attacks carefully

Decision Making:
- Antidote: Save if victim is valuable or you suspect they're seer/guardian
- Poison: Use on confirmed werewolves or very suspicious players
- Consider saving abilities for late game
- Don't waste poison on villagers"""

    def night_action_save(self, victim: str, context: str) -> bool:
        """Decide whether to save the victim"""
        if self.antidote_used:
            return False

        # Record victim information
        self.night_victims.append(
            {"victim": victim, "round": len(self.night_victims) + 1}
        )

        prompt = f"""Night Phase - Witch's Decision (Antidote)

The werewolves have attacked: {victim}

Context:
{context}

Previous night victims:
{self._format_night_history()}

You have ONE antidote. Should you use it to save {victim}?
Strategy guidelines for your role:
{self._format_strategy_rules()}

Consider:
1. Is {victim} a valuable player?
2. Could {victim} be the seer or other important role?
3. Should you save the antidote for later?
4. Would guardian protect it instead?

Decision (YES/NO):"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        decision = "YES" in _extract_text_content(response).upper()

        if decision:
            self.antidote_used = True
            self.saved_player = victim
        return decision

    def _format_night_history(self) -> str:
        """Format night victim history"""
        if not self.night_victims:
            return "No night attacks recorded yet"
        return "\n".join(
            [
                f"Night {v['round']}: {v['victim']} was attacked"
                for v in self.night_victims
            ]
        )

    def night_action_poison(self, context: str, targets: List[str]) -> Optional[str]:
        """Decide whether to poison someone"""
        if self.poison_used:
            return None

        prompt = f"""Night Phase - Witch's Decision (Poison)

Possible targets: {', '.join(targets)}

Context:
{context}

Antidote status: {'USED' if self.antidote_used else 'AVAILABLE'}
Poison status: AVAILABLE (one-time use)

Should you use your poison tonight? If yes, who?
Strategy guidelines for your role:
{self._format_strategy_rules()}

Consider:
1. Do you have confirmed werewolves?
2. Is it worth using poison now?
3. Could you save it for a better opportunity?

Decision: POISON: [player_name] or PASS"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )

        if "PASS" in _extract_text_content(response).upper():
            return None

        target = self._extract_choice(_extract_text_content(response), targets)
        if target:
            self.poison_used = True
            self.poisoned_player = target
        return target

    def _extract_choice(self, response: str, valid_players: List[str]) -> Optional[str]:
        response_upper = response.upper()
        for player in valid_players:
            if player.upper() in response_upper:
                return player
        return None

    def discuss(self, context: str, discussion_history: List[Msg]) -> str:
        """Participate in day discussion as witch"""
        prompt = f"""Current game context:
{context}

Recent discussion:
{self._format_discussion(discussion_history)}

You're the witch but pretending to be a regular villager. Speak naturally like in a conversation (2-4 sentences). Share your thoughts without revealing your role.

Strategy guidelines for your role:
{self._format_strategy_rules()}

IMPORTANT: Just provide your statement directly. Do NOT start with your name.

Your statement:"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return _extract_text_content(response)

    def vote(self, context: str, alive_players: List[str]) -> str:
        """Vote for a player to eliminate"""
        prompt = f"""Current game context:
{context}

Alive players: {', '.join(alive_players)}

Based on all discussions and your secret knowledge as the witch, who should be voted out?
Strategy guidelines for your role:
{self._format_strategy_rules()}

Format: VOTE: [player_name]
Reasoning: [your reasoning]"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return self._extract_vote(_extract_text_content(response), alive_players)

    def _format_discussion(self, messages: List[Msg]) -> str:
        if not messages:
            return "No discussion yet."
        return "\n".join([f"{msg.name}: {msg.content}" for msg in messages[-10:]])

    def _extract_vote(self, response: str, valid_players: List[str]) -> str:
        response_upper = response.upper()
        for player in valid_players:
            if player.upper() in response_upper:
                return player
        return valid_players[0] if valid_players else ""


class GuardianAgent(WerewolfAgentBase):
    """Guardian agent - can protect one player each night"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_protected: Optional[str] = None

    def _get_default_sys_prompt(self) -> str:
        return """You are the GUARDIAN in the Werewolf game.

Your Role:
- You are on the good side
- Each night, you can protect one player from werewolf attacks
- You CANNOT protect the same player two nights in a row
- You can protect yourself

Strategy:
1. Protect players who seem valuable or are seer candidates
2. Vary your protection pattern
3. Consider protecting yourself when threatened
4. Protect active discussants who might be targeted
5. Keep your role secret

Protection Priority:
- Suspected seer or witch
- Active and influential villagers
- Yourself if under suspicion
- Random rotation to avoid patterns"""

    def night_action(self, context: str, targets: List[str]) -> str:
        """Choose player to protect"""
        available = [t for t in targets if t != self.last_protected]

        prompt = f"""Night Phase - Guardian's Protection

Available targets: {', '.join(available)}
{'Last protected: ' + self.last_protected if self.last_protected else 'First night'}

Context:
{context}

Strategy guidelines for your role:
{self._format_strategy_rules()}

Who should you protect tonight? Consider:
1. Who is most likely to be targeted?
2. Who seems like they might be the seer?
3. Should you protect yourself?
4. Vary your pattern to be unpredictable

Your choice:"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        choice = self._extract_choice(_extract_text_content(response), available)
        self.last_protected = choice
        return choice

    def _extract_choice(self, response: str, valid_players: List[str]) -> str:
        response_upper = response.upper()
        for player in valid_players:
            if player.upper() in response_upper:
                return player
        return valid_players[0] if valid_players else ""

    def discuss(self, context: str, discussion_history: List[Msg]) -> str:
        """Participate in day discussion as guardian"""
        prompt = f"""Current game context:
{context}

Recent discussion:
{self._format_discussion(discussion_history)}

You're the guardian but pretending to be a regular villager. Speak naturally like in a conversation (2-4 sentences). Share your thoughts without revealing your role.

Strategy guidelines for your role:
{self._format_strategy_rules()}

IMPORTANT: Just provide your statement directly. Do NOT start with your name.

Your statement:"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return _extract_text_content(response)

    def vote(self, context: str, alive_players: List[str]) -> str:
        """Vote for a player to eliminate"""
        prompt = f"""Current game context:
{context}

Alive players: {', '.join(alive_players)}

Based on all discussions and your protection patterns, who should be voted out?
Strategy guidelines for your role:
{self._format_strategy_rules()}

Format: VOTE: [player_name]
Reasoning: [your reasoning]"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return self._extract_vote(_extract_text_content(response), alive_players)

    def _format_discussion(self, messages: List[Msg]) -> str:
        if not messages:
            return "No discussion yet."
        return "\n".join([f"{msg.name}: {msg.content}" for msg in messages[-10:]])

    def _extract_vote(self, response: str, valid_players: List[str]) -> str:
        response_upper = response.upper()
        for player in valid_players:
            if player.upper() in response_upper:
                return player
        return valid_players[0] if valid_players else ""

    def last_words(self, context: str, cause_of_death: str) -> str:
        """Guardian's last words - can mention protection patterns"""
        protection_history = []
        if hasattr(self, "last_protected") and self.last_protected:
            protection_history.append(f"Last protected: {self.last_protected}")

        prompt = f"""You are about to die in the Werewolf game.
        
Your Role: {self.role.value}
Cause of Death: {cause_of_death}
{chr(10).join(protection_history) if protection_history else ""}

Game Context:
{context}

CRITICAL: You can share information about who you protected to help villagers deduce information.
- Mentioning who you protected can help confirm they're not werewolves
- Revealing protection patterns might help identify who survived werewolf attacks
- Be careful not to mislead your team

This is your last chance to speak. What are your final words?

Your last words (keep it brief, 2-3 sentences):"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return _extract_text_content(response)


class HunterAgent(WerewolfAgentBase):
    """Hunter agent - can shoot someone when dying (except by witch poison)"""

    def _get_default_sys_prompt(self) -> str:
        return """You are the HUNTER in the Werewolf game.

Your Role:
- You are on the good side
- When you die (except by witch poison), you can shoot and kill one player
- This is your revenge ability - use it wisely

Strategy During Game:
1. Participate in discussions like a villager
2. Try to identify werewolves
3. Don't reveal you're the hunter too early
4. Vote to eliminate suspicious players

Strategy When Dying:
1. If killed by werewolves or voted out, you MUST shoot someone
2. Shoot confirmed or suspected werewolves
3. Don't shoot randomly - make it count
4. Consider information from seer or other sources"""

    def shoot_target(
        self, context: str, alive_players: List[str], cause_of_death: str
    ) -> str:
        """Choose who to shoot when dying

        Args:
            context: Current game context
            alive_players: List of players still alive
            cause_of_death: How the hunter died
        """
        prompt = f"""You are the HUNTER and you are dying!

Cause of Death: {cause_of_death}

Game Context:
{context}

Alive Players: {', '.join(alive_players)}

You can shoot ONE player before you die. Who do you choose?
Strategy guidelines for your role:
{self._format_strategy_rules()}

Consider:
1. Shoot suspected werewolves
2. Use information from discussions
3. Make this shot count - it's your final contribution

Your choice (just the player name):"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return self._extract_choice(_extract_text_content(response), alive_players)

    def _extract_choice(self, response: str, valid_players: List[str]) -> str:
        response_upper = response.upper()
        for player in valid_players:
            if player.upper() in response_upper:
                return player
        return valid_players[0] if valid_players else ""

    def discuss(self, context: str, discussion_history: List[Msg]) -> str:
        """Participate in day discussion as hunter (pretending to be villager)"""
        prompt = f"""Current game context:
{context}

Recent discussion:
{self._format_discussion(discussion_history)}

You're the hunter but pretending to be a regular villager. Speak naturally like in a conversation (2-4 sentences). Share your thoughts without revealing your role.

Strategy guidelines for your role:
{self._format_strategy_rules()}

IMPORTANT: Just provide your statement directly. Do NOT start with your name.

Your statement:"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return _extract_text_content(response)

    def vote(self, context: str, alive_players: List[str]) -> str:
        """Vote for a player to eliminate"""
        prompt = f"""Current game context:
{context}

Alive players: {', '.join(alive_players)}

Based on all discussions, who should be voted out?
Strategy guidelines for your role:
{self._format_strategy_rules()}

Format: VOTE: [player_name]
Reasoning: [your reasoning]"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return self._extract_vote(_extract_text_content(response), alive_players)

    def _format_discussion(self, messages: List[Msg]) -> str:
        if not messages:
            return "No discussion yet."
        return "\n".join([f"{msg.name}: {msg.content}" for msg in messages[-10:]])

    def _extract_vote(self, response: str, valid_players: List[str]) -> str:
        response_upper = response.upper()
        for player in valid_players:
            if player.upper() in response_upper:
                return player
        return valid_players[0] if valid_players else ""


def create_agent(
    name: str,
    role: Role,
    model_config_name: str,
    strategy_rules: List[str] | None = None,
) -> WerewolfAgentBase:
    """Factory function to create appropriate agent based on role"""
    agent_classes = {
        Role.VILLAGER: VillagerAgent,
        Role.WEREWOLF: WerewolfAgent,
        Role.SEER: SeerAgent,
        Role.WITCH: WitchAgent,
        Role.GUARDIAN: GuardianAgent,
        Role.HUNTER: HunterAgent,
    }

    agent_class = agent_classes.get(role, VillagerAgent)
    agent = agent_class(name=name, role=role, model_config_name=model_config_name)
    if strategy_rules:
        agent.set_strategy_rules(strategy_rules)
    return agent
