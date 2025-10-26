"""
Multi-Agent Werewolf Game Orchestrator
Integrates WerewolfGame logic with AgentScope intelligent agents
"""

import logging
from typing import Dict, List, Any, Optional

from agentscope.message import Msg

from .WerewolfGame import WerewolfGame, Role, GamePhase
from .agents import create_agent, WerewolfAgentBase, WerewolfAgent


class WerewolfGameOrchestrator:
    """
    Orchestrates a multi-agent Werewolf game using AgentScope
    Manages game flow, agent interactions, and state updates
    """

    def __init__(
        self,
        player_names: List[str],
        model_config_name: str,
        game_type: str = "six",
        max_rounds: int = 20,
        discussion_rounds: int = 3,
        verbose: bool = True,
    ):
        """
        Initialize the game orchestrator

        Args:
            player_names: List of player names
            model_config_name: AgentScope model configuration name
            game_type: Game type (six, nine, twelve)
            max_rounds: Maximum number of day/night cycles
            discussion_rounds: Number of discussion rounds per day
            verbose: Whether to print game progress
        """
        self.game = WerewolfGame(player_names, game_type)
        self.model_config_name = model_config_name
        self.max_rounds = max_rounds
        self.discussion_rounds = discussion_rounds
        self.verbose = verbose

        # Create agents
        self.agents: Dict[str, WerewolfAgentBase] = {}
        self._create_agents()

        # Game state
        self.current_round = 0
        self.discussion_history: List[Msg] = []

        # Setup logging
        self.logger = logging.getLogger(__name__)
        if verbose:
            self.logger.setLevel(logging.INFO)

    def _create_agents(self):
        """Create AI agents for each player"""
        for player_name in self.game.player_names:
            role = self.game.state.roles[player_name]
            agent = create_agent(player_name, role, self.model_config_name)
            self.agents[player_name] = agent

        # Share werewolf team information
        werewolves = [
            name
            for name, role in self.game.state.roles.items()
            if role == Role.WEREWOLF
        ]
        for wolf_name in werewolves:
            self.agents[wolf_name].known_roles.update(
                {w: Role.WEREWOLF for w in werewolves}
            )

        self._log(f"Created {len(self.agents)} agents")
        self._log(f"Werewolf team: {', '.join(werewolves)}")

    def run_game(self) -> str:
        """
        Run the complete game until win condition
        Returns: Winner ('werewolves' or 'villagers')
        """
        self._log("=" * 60)
        self._log("WEREWOLF GAME STARTING")
        self._log("=" * 60)

        while self.current_round < self.max_rounds:
            self.current_round += 1
            self._log(f"\n{'='*60}")
            self._log(f"ROUND {self.current_round}")
            self._log(f"{'='*60}")

            # Night phase
            self._log("\n🌙 NIGHT PHASE")
            self._run_night_phase()

            # Check game end
            ended, winner = self.game.check_game_end()
            if ended:
                self._log_game_end(winner)
                return winner

            # Day phase
            self._log("\n☀️ DAY PHASE")
            self._run_day_phase()

            # Check game end
            ended, winner = self.game.check_game_end()
            if ended:
                self._log_game_end(winner)
                return winner

        self._log("\n⏰ Maximum rounds reached - Game ended in draw")
        return "draw"

    def _run_night_phase(self):
        """Execute night phase with all night actions"""
        agent_actions: Dict[str, str] = {}

        # Werewolf actions
        self._log("\n🐺 Werewolves choosing target...")
        werewolf_agents = [
            agent
            for agent in self.agents.values()
            if agent.role == Role.WEREWOLF and agent.is_alive
        ]

        if werewolf_agents:
            # Get werewolf targets
            targets = [
                p
                for p in self.game.state.alive_players
                if self.game.state.roles[p] != Role.WEREWOLF
            ]

            if targets:
                context = self._get_game_context()
                werewolf_names = [w.name for w in werewolf_agents]

                # Each werewolf votes
                for wolf in werewolf_agents:
                    target = wolf.night_action(context, targets, werewolf_names)
                    agent_actions[wolf.name] = target
                    self._log(f"  {wolf.name} targets: {target}")

        # Seer actions
        self._log("\n🔮 Seer checking...")
        seer_agents = [
            agent
            for agent in self.agents.values()
            if agent.role == Role.SEER and agent.is_alive
        ]

        for seer in seer_agents:
            targets = [p for p in self.game.state.alive_players if p != seer.name]
            if targets:
                context = self._get_game_context()
                target = seer.night_action(context, targets)
                agent_actions[seer.name] = target
                self._log(f"  {seer.name} checks: {target}")

        # Guardian actions
        self._log("\n🛡️ Guardian protecting...")
        guardian_agents = [
            agent
            for agent in self.agents.values()
            if agent.role == Role.GUARDIAN and agent.is_alive
        ]

        for guardian in guardian_agents:
            targets = self.game.state.alive_players.copy()
            context = self._get_game_context()
            target = guardian.night_action(context, targets)
            agent_actions[guardian.name] = target
            self._log(f"  {guardian.name} protects: {target}")

        # Execute night phase in game
        night_result = self.game.execute_night_phase(agent_actions)

        # Update seer knowledge
        if "seer_checks" in night_result:
            for seer_name, checked_role in night_result["seer_checks"].items():
                target = agent_actions.get(seer_name)
                if target and seer_name in self.agents:
                    self.agents[seer_name].known_roles[target] = checked_role

        # Witch actions (after knowing victim)
        self._log("\n🧪 Witch deciding...")
        witch_agents = [
            agent
            for agent in self.agents.values()
            if agent.role == Role.WITCH and agent.is_alive
        ]

        for witch in witch_agents:
            victim = night_result.get("werewolf_target")
            context = self._get_game_context()

            # Decide on antidote
            if victim and not witch.antidote_used:
                should_save = witch.night_action_save(victim, context)
                if should_save:
                    agent_actions[witch.name] = "save"
                    self._log(f"  {witch.name} saves {victim}")

            # Decide on poison
            if not witch.poison_used:
                targets = [p for p in self.game.state.alive_players if p != witch.name]
                poison_target = witch.night_action_poison(context, targets)
                if poison_target:
                    agent_actions[witch.name] = f"poison:{poison_target}"
                    self._log(f"  {witch.name} poisons {poison_target}")

        # Re-execute with witch actions
        if any(w.role == Role.WITCH and w.is_alive for w in self.agents.values()):
            night_result = self.game.execute_night_phase(agent_actions)

        # Update agent states
        self._update_agents_after_night(night_result)

        # Announce results
        self._announce_night_results(night_result)

    def _run_day_phase(self):
        """Execute day phase with discussion and voting"""
        self._log(f"\n💬 Day {self.game.state.day_count + 1} Discussion")
        self._log(f"Alive players: {', '.join(self.game.state.alive_players)}")

        # Discussion rounds
        for round_num in range(self.discussion_rounds):
            self._log(f"\n--- Discussion Round {round_num + 1} ---")

            alive_agents = [agent for agent in self.agents.values() if agent.is_alive]

            for agent in alive_agents:
                context = self._get_game_context()
                statement = agent.discuss(context, self.discussion_history[-20:])

                msg = Msg(name=agent.name, content=statement, role="assistant")
                self.discussion_history.append(msg)

                self._log(f"{agent.name}: {statement[:100]}...")

        # Voting
        self._log("\n🗳️ Voting Phase")
        agent_votes: Dict[str, str] = {}

        alive_agents = [agent for agent in self.agents.values() if agent.is_alive]
        for agent in alive_agents:
            context = self._get_game_context()
            vote = agent.vote(context, self.game.state.alive_players)
            agent_votes[agent.name] = vote
            self._log(f"  {agent.name} votes for: {vote}")

        # Execute day phase
        day_result = self.game.execute_day_phase(agent_votes)

        # Update agent states
        self._update_agents_after_day(day_result)

        # Announce results
        eliminated = day_result.get("eliminated")
        if eliminated:
            self._log(f"\n⚰️ {eliminated} was eliminated by vote!")
            self._log(f"   Role: {self.game.state.roles[eliminated].value}")
        else:
            self._log("\n🤝 No one was eliminated (tie vote)")

    def _update_agents_after_night(self, night_result: Dict[str, Any]):
        """Update agent states after night phase"""
        # Mark dead agents
        for agent_name, agent in self.agents.items():
            if agent_name not in self.game.state.alive_players:
                agent.mark_dead()

    def _update_agents_after_day(self, day_result: Dict[str, Any]):
        """Update agent states after day phase"""
        eliminated = day_result.get("eliminated")
        if eliminated and eliminated in self.agents:
            self.agents[eliminated].mark_dead()

    def _announce_night_results(self, night_result: Dict[str, Any]):
        """Announce what happened during the night"""
        victim = night_result.get("werewolf_target")
        saved = night_result.get("saved")
        poisoned = night_result.get("poisoned")

        self._log("\n📰 Morning Announcement:")

        deaths = []
        for player in self.game.player_names:
            if (
                player not in self.game.state.alive_players
                and self.agents[player].is_alive
            ):
                deaths.append(player)
                self.agents[player].mark_dead()

        if deaths:
            for dead in deaths:
                self._log(f"  💀 {dead} died during the night")
        else:
            self._log("  ✨ Everyone survived the night!")

    def _get_game_context(self) -> str:
        """Generate context string for agents"""
        context = f"""Round: {self.current_round}
Phase: {self.game.state.phase.value}
Day: {self.game.state.day_count}

Alive Players ({len(self.game.state.alive_players)}):
{', '.join(self.game.state.alive_players)}

Recent Events:
{chr(10).join(self.game.state.game_log[-5:])}"""
        return context

    def _log(self, message: str):
        """Log message if verbose"""
        if self.verbose:
            print(message)
            self.logger.info(message)

    def _log_game_end(self, winner: str):
        """Log game end information"""
        self._log("\n" + "=" * 60)
        self._log("GAME OVER")
        self._log("=" * 60)
        self._log(f"🏆 Winner: {winner.upper()}")
        self._log(f"Rounds played: {self.current_round}")
        self._log(f"\n📊 Final Roles:")
        for player, role in self.game.state.roles.items():
            status = "💀" if player not in self.game.state.alive_players else "✅"
            self._log(f"  {status} {player}: {role.value}")

    def get_game_summary(self) -> Dict[str, Any]:
        """Get complete game summary"""
        return {
            "rounds": self.current_round,
            "winner": self.game.check_game_end()[1],
            "final_state": self.game.to_dict(),
            "roles": {p: r.value for p, r in self.game.state.roles.items()},
            "survivors": self.game.state.alive_players,
            "game_log": self.game.state.game_log,
        }
