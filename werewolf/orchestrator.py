"""
Multi-Agent Werewolf Game Orchestrator
Integrates WerewolfGame logic with AgentScope intelligent agents
"""

import logging
from typing import Dict, List, Any, Optional

from agentscope.message import Msg

from .werewolf_game import WerewolfGame, Role, GamePhase
from .agents import create_agent, WerewolfAgentBase, WerewolfAgent
from .learning_engine import StrategyManager, run_learning_pipeline


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
        discussion_rounds: int = 1,  # Fixed to 1 discussion round
        verbose: bool = True,
        log_file: str = None,
    ):
        """
        Initialize the game orchestrator

        Args:
            player_names: List of player names
            model_config_name: AgentScope model configuration name
            game_type: Game type (six, nine, twelve)
            max_rounds: Maximum number of day/night cycles
            discussion_rounds: Number of discussion rounds per day (FIXED to 1)
            verbose: Whether to print game progress
            log_file: Path to log file for real-time writing
        """
        self.game = WerewolfGame(player_names, game_type)
        self.model_config_name = model_config_name
        self.max_rounds = max_rounds
        self.discussion_rounds = 1  # Always 1, ignore parameter
        self.verbose = verbose

        # Setup logging (must be before _create_agents which uses _log)
        self.logger = logging.getLogger(__name__)
        if verbose:
            self.logger.setLevel(logging.INFO)

        # Game state
        self.current_round = 0
        self.discussion_history: List[Msg] = []

        # Real-time log file
        import datetime
        import os

        # Create logs directory if it doesn't exist
        log_dir = "game_logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        if log_file is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"werewolf_game_{timestamp}.txt")
        self.log_file = log_file

        # Game record for saving complete transcript (must be before _create_agents)
        self.game_record: List[str] = []
        self.game_record.append("=" * 80)
        self.game_record.append("WEREWOLF GAME - COMPLETE TRANSCRIPT")
        self.game_record.append("=" * 80)
        self.game_record.append(f"Game Type: {game_type}")
        self.game_record.append(f"Players: {', '.join(player_names)}")
        self.game_record.append("=" * 80)
        self.game_record.append("")

        # Write initial header to log file
        self._write_to_log_file()

        # Create agents (uses _log which needs game_record)
        self.agents: Dict[str, WerewolfAgentBase] = {}
        self._create_agents()

    def _create_agents(self):
        """Create AI agents for each player"""
        strategy_manager = StrategyManager()
        for player_name in self.game.player_names:
            role = self.game.state.roles[player_name]
            # Load persisted strategy rules for this role, if any
            rules = strategy_manager.load_rules_for_role(role.value)
            agent = create_agent(
                player_name, role, self.model_config_name, strategy_rules=rules
            )
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
            self._log("\n[NIGHT PHASE]")
            self._run_night_phase()

            # Check game end
            ended, winner = self.game.check_game_end()
            if ended:
                self._log_game_end(winner)
                return winner

            # Day phase
            self._log("\n[DAY PHASE]")
            self._run_day_phase()

            # Check game end
            ended, winner = self.game.check_game_end()
            if ended:
                self._log_game_end(winner)
                return winner

        self._log("\n[TIME UP] Maximum rounds reached - Game ended in draw")
        return "draw"

    def _run_night_phase(self):
        """Execute night phase with all night actions in order: Guardian -> Werewolf -> Seer -> Witch"""
        agent_actions: Dict[str, str] = {}

        # 1. Guardian actions (first)
        self._log("\n[GUARDIAN] Protecting...")
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

        # 2. Werewolf actions (second)
        self._log("\n[WEREWOLVES] Choosing target...")
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

        # 3. Seer actions (third)
        self._log("\n[SEER] Checking...")
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

        # Execute night phase in game
        night_result = self.game.execute_night_phase(agent_actions)

        # Update seer knowledge and log results
        if "seer_checks" in night_result:
            for seer_name, checked_role in night_result["seer_checks"].items():
                target = agent_actions.get(seer_name)
                if target and seer_name in self.agents:
                    # Seer learns the actual role for internal tracking
                    self.agents[seer_name].known_roles[target] = checked_role
                    # But only announce team (good/bad) in logs for learning
                    team = checked_role.get_team()
                    self._log(f"  {seer_name} learned: {target} is {team}")

        # Witch actions (after knowing victim)
        self._log("\n[WITCH] Deciding...")
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
                else:
                    self._log(f"  {witch.name} does not save {victim}")

            # Decide on poison
            if not witch.poison_used:
                targets = [p for p in self.game.state.alive_players if p != witch.name]
                poison_target = witch.night_action_poison(context, targets)
                if poison_target:
                    agent_actions[witch.name] = f"poison:{poison_target}"
                    self._log(f"  {witch.name} poisons {poison_target}")
                else:
                    self._log(f"  {witch.name} does not use poison")

        # Re-execute with witch actions
        if any(w.role == Role.WITCH and w.is_alive for w in self.agents.values()):
            night_result = self.game.execute_night_phase(agent_actions)

        # Update agent states
        self._update_agents_after_night(night_result)

        # Announce results
        self._announce_night_results(night_result)

    def _run_day_phase(self):
        """Execute day phase with discussion and voting"""
        self._log(f"\n[DISCUSSION] Day {self.game.state.day_count + 1}")
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

                # Log complete statement without truncation
                self._log(f"{agent.name}: {statement}")

        # Voting
        self._log("\n[VOTING] Voting Phase")
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
            self._log(f"\n[ELIMINATED] {eliminated} was eliminated by vote!")
            self._log(f"   Role: {self.game.state.roles[eliminated].value}")

            # Last words for voted out player
            if eliminated in self.agents:
                self._log(f"\n[LAST WORDS] {eliminated}'s final statement:")
                context = self._get_game_context()
                last_words = self.agents[eliminated].last_words(context, "voted_out")
                self._log(f"  {eliminated}: {last_words}")

            # Hunter shoots if killed by vote (not by witch poison)
            if (
                self.game.state.roles.get(eliminated) == Role.HUNTER
                and self.game.state.death_records.get(eliminated) == "voted_out"
            ):
                self._log(f"\n[HUNTER SKILL] {eliminated} activates hunter ability!")
                if eliminated in self.agents and self.game.state.alive_players:
                    from .agents import HunterAgent

                    if isinstance(self.agents[eliminated], HunterAgent):
                        context = self._get_game_context()
                        target = self.agents[eliminated].shoot_target(
                            context, self.game.state.alive_players.copy(), "voted_out"
                        )
                        if target and target in self.game.state.alive_players:
                            self._log(f"  {eliminated} shoots {target}!")
                            self.game.state.alive_players.remove(target)
                            self.game.state.death_records[target] = "hunter_shot"
                            self.agents[target].mark_dead()
                            self._log(
                                f"  {target} ({self.game.state.roles[target].value}) is killed!"
                            )
        else:
            self._log("\n[TIE] No one was eliminated (tie vote)")

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
        """Announce what happened during the night, including last words and hunter shots"""
        victim = night_result.get("werewolf_target")
        saved = night_result.get("saved")
        poisoned = night_result.get("poisoned")

        self._log("\n[MORNING] Announcement:")

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
                cause = self.game.state.death_records.get(dead, "unknown")
                self._log(f"  [DEAD] {dead} died during the night ({cause})")

                # Last words for night deaths
                if dead in self.agents:
                    self._log(f"\n[LAST WORDS] {dead}'s final statement:")
                    context = self._get_game_context()
                    last_words = self.agents[dead].last_words(context, cause)
                    self._log(f"  {dead}: {last_words}")

                # Hunter shoots if killed by werewolves (not by witch poison)
                if (
                    self.game.state.roles.get(dead) == Role.HUNTER
                    and cause == "werewolf_kill"
                ):
                    self._log(f"\n[HUNTER SKILL] {dead} activates hunter ability!")
                    if dead in self.agents and self.game.state.alive_players:
                        from .agents import HunterAgent

                        if isinstance(self.agents[dead], HunterAgent):
                            context = self._get_game_context()
                            target = self.agents[dead].shoot_target(
                                context, self.game.state.alive_players.copy(), cause
                            )
                            if target and target in self.game.state.alive_players:
                                self._log(f"  {dead} shoots {target}!")
                                self.game.state.alive_players.remove(target)
                                self.game.state.death_records[target] = "hunter_shot"
                                self.agents[target].mark_dead()
                                self._log(
                                    f"  {target} ({self.game.state.roles[target].value}) is killed!"
                                )
        else:
            self._log("  [SAFE] Everyone survived the night!")

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
        """Log message if verbose, save to game record, and write to file in real-time"""
        # Save to game record
        self.game_record.append(message)

        # Write to file immediately
        self._write_to_log_file(message)

        # Print if verbose
        if self.verbose:
            print(message)
            self.logger.info(message)

    def _write_to_log_file(self, message: str = None):
        """Write message to log file immediately

        Args:
            message: Single message to append. If None, write entire game_record
        """
        try:
            if message is None:
                # Write entire game record (used for initialization)
                with open(self.log_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(self.game_record))
            else:
                # Append single message
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(message + "\n")
        except Exception as e:
            if self.verbose:
                print(f"Warning: Failed to write to log file: {e}")

    def _log_game_end(self, winner: str):
        """Log game end information"""
        self._log("\n" + "=" * 60)
        self._log("GAME OVER")
        self._log("=" * 60)
        self._log(f"[WINNER] {winner.upper()}")
        self._log(f"Rounds played: {self.current_round}")
        self._log(f"\n[FINAL ROLES]")
        for player, role in self.game.state.roles.items():
            status = (
                "[DEAD]" if player not in self.game.state.alive_players else "[ALIVE]"
            )
            self._log(f"  {status} {player}: {role.value}")

        # After logging, run learning engine to analyze the game and update strategies
        try:
            # Pick any agent's model for analysis
            model_for_learning = None
            if self.agents:
                model_for_learning = next(iter(self.agents.values())).model
            if model_for_learning:
                review_dir = run_learning_pipeline(
                    self.log_file,
                    self.agents,
                    self.game.state.roles,
                    model_for_learning,
                )
                self._log(f"\n[LEARNING] Reviews and lessons saved to: {review_dir}")
            else:
                self._log("\n[LEARNING] Skipped (no model available)")
        except Exception as e:
            self._log(f"\n[LEARNING] Failed: {e}")

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

    def save_game_record(self, filename: str = None):
        """Save complete game record to file

        Args:
            filename: Output filename. If None, auto-generate based on timestamp
        """
        import datetime

        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"werewolf_game_{timestamp}.txt"

        # Add final summary to record
        self.game_record.append("\n" + "=" * 80)
        self.game_record.append("GAME STATISTICS")
        self.game_record.append("=" * 80)
        self.game_record.append(f"Total Rounds: {self.current_round}")
        self.game_record.append(f"Winner: {self.game.check_game_end()[1]}")
        self.game_record.append(f"\nRole Assignments:")
        for player, role in sorted(self.game.state.roles.items()):
            status = "DEAD" if player not in self.game.state.alive_players else "ALIVE"
            self.game_record.append(f"  {player}: {role.value} ({status})")
        self.game_record.append("=" * 80)

        # Write to file
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(self.game_record))

        self._log(f"\nGame record saved to: {filename}")
        return filename
