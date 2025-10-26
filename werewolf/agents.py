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


from .WerewolfGame import Role, GamePhase


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


def _run_model_sync(model, msg_list):
    """Synchronous wrapper for async model calls

    Args:
        model: The AgentScope model instance
        msg_list: List of Msg objects to send to the model
    """
    try:
        # Get or create event loop
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # No event loop in current thread, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Convert Msg objects to dict format expected by model
    # AgentScope 1.0 models expect list of dicts with 'role' and 'content'
    messages = []
    for msg in msg_list:
        if hasattr(msg, "to_dict"):
            msg_dict = msg.to_dict()
            messages.append({"role": msg_dict["role"], "content": msg_dict["content"]})
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

As a villager, analyze the situation and respond. Consider:
1. Who seems suspicious and why?
2. Who are you trusting and why?
3. What questions should you ask?

Your response:"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return _extract_text_content(response)

    def vote(self, context: str, alive_players: List[str]) -> str:
        """Vote for a player to eliminate"""
        prompt = f"""Current game context:
{context}

Alive players: {', '.join(alive_players)}

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

As a werewolf PRETENDING to be a villager:
1. Act like you're trying to find werewolves
2. Subtly deflect suspicion from yourself and allies
3. Build trust with real villagers
4. Don't be too obvious

Your response (stay in character as innocent villager):"""

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

    def _extract_vote(self, response: str, valid_players: List[str]) -> str:
        response_upper = response.upper()
        for player in valid_players:
            if player.upper() in response_upper:
                return player
        return valid_players[0] if valid_players else ""

    def vote(self, context: str, alive_players: List[str]) -> str:
        """Vote for a player to eliminate (as werewolf pretending to be villager)"""
        prompt = f"""Current game context:
{context}

Alive players: {', '.join(alive_players)}

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
        prompt = f"""Night Phase - Seer's Check

Possible targets: {', '.join(targets)}

Context:
{context}

Players you've already checked:
{self._format_known_roles()}

Who should you check tonight? Consider:
1. Most suspicious players from discussions
2. Players you haven't checked yet
3. Key players in leadership positions

Your choice:"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        return self._extract_choice(_extract_text_content(response), targets)

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

As the seer, guide the discussion WITHOUT revealing your role too obviously.
{'Focus on eliminating: ' + ', '.join(known_wolves) if known_wolves else 'Share observations carefully.'}

Your response:"""

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

        prompt = f"""Night Phase - Witch's Decision (Antidote)

The werewolves have attacked: {victim}

Context:
{context}

You have ONE antidote. Should you use it to save {victim}?
Consider:
1. Is {victim} a valuable player?
2. Could {victim} be the seer or other important role?
3. Should you save the antidote for later?

Decision (YES/NO):"""

        response = _run_model_sync(
            self.model, [Msg(name=self.name, content=prompt, role="user")]
        )
        decision = "YES" in _extract_text_content(response).upper()

        if decision:
            self.antidote_used = True
        return decision

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

As the witch (but pretending to be a regular villager), analyze the situation and respond.
Consider:
1. Who seems suspicious and why?
2. Use your knowledge of who was attacked at night carefully
3. Don't reveal your role unless absolutely necessary

Your response:"""

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

As the guardian (but pretending to be a regular villager), analyze the situation and respond.
Consider:
1. Who seems suspicious and why?
2. Use your protection knowledge carefully
3. Don't reveal your role unless absolutely necessary

Your response:"""

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


def create_agent(name: str, role: Role, model_config_name: str) -> WerewolfAgentBase:
    """Factory function to create appropriate agent based on role"""
    agent_classes = {
        Role.VILLAGER: VillagerAgent,
        Role.WEREWOLF: WerewolfAgent,
        Role.SEER: SeerAgent,
        Role.WITCH: WitchAgent,
        Role.GUARDIAN: GuardianAgent,
        Role.HUNTER: VillagerAgent,  # Hunter uses villager logic for now
    }

    agent_class = agent_classes.get(role, VillagerAgent)
    return agent_class(name=name, role=role, model_config_name=model_config_name)
