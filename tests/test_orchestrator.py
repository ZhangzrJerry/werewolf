"""
Unit tests for WerewolfGameOrchestrator

Tests game flow, night phase execution, logging, and learning pipeline
"""

import sys
import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, call

# Mock agentscope before importing orchestrator
sys.modules["agentscope"] = MagicMock()
sys.modules["agentscope.message"] = MagicMock()

from werewolf.orchestrator import WerewolfGameOrchestrator
from werewolf.werewolf_game import Role


class TestOrchestratorInit(unittest.TestCase):
    """Test orchestrator initialization"""

    @patch("werewolf.orchestrator.WerewolfGame")
    @patch("werewolf.orchestrator.create_agent")
    def test_orchestrator_creation(self, mock_create_agent, mock_game):
        """Test that orchestrator can be created"""
        mock_game_instance = Mock()
        mock_game.return_value = mock_game_instance
        mock_game_instance.player_names = [
            "Alice",
            "Bob",
            "Charlie",
            "David",
            "Eve",
            "Frank",
        ]
        mock_game_instance.state.roles = {
            "Alice": Role.VILLAGER,
            "Bob": Role.WEREWOLF,
            "Charlie": Role.WEREWOLF,
            "David": Role.SEER,
            "Eve": Role.WITCH,
            "Frank": Role.VILLAGER,
        }

        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent

        # Use temporary log file to avoid creating .training directory
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "test_game.txt")

        try:
            players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
            orchestrator = WerewolfGameOrchestrator(
                players, "test_model", game_type="six", verbose=False, log_file=log_file
            )

            self.assertIsNotNone(orchestrator)
            self.assertEqual(orchestrator.model_config_name, "test_model")
            self.assertEqual(orchestrator.discussion_rounds, 1)  # Always 1
        finally:
            shutil.rmtree(temp_dir)

    @patch("werewolf.orchestrator.WerewolfGame")
    @patch("werewolf.orchestrator.create_agent")
    def test_werewolf_team_info_shared(self, mock_create_agent, mock_game):
        """Test that werewolves know each other"""
        mock_game_instance = Mock()
        mock_game.return_value = mock_game_instance
        mock_game_instance.player_names = [
            "Alice",
            "Bob",
            "Charlie",
            "David",
            "Eve",
            "Frank",
        ]
        mock_game_instance.state.roles = {
            "Alice": Role.WEREWOLF,
            "Bob": Role.WEREWOLF,
            "Charlie": Role.VILLAGER,
            "David": Role.SEER,
            "Eve": Role.WITCH,
            "Frank": Role.VILLAGER,
        }

        mock_agents = {}

        def create_mock_agent(name, role, model, strategy_rules=None):
            agent = Mock()
            agent.name = name
            agent.role = role
            agent.known_roles = {name: role}
            mock_agents[name] = agent
            return agent

        mock_create_agent.side_effect = create_mock_agent

        # Use temporary log file to avoid creating .training directory
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "test_game.txt")

        try:
            players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
            orchestrator = WerewolfGameOrchestrator(
                players, "test_model", game_type="six", verbose=False, log_file=log_file
            )

            # Check that werewolves know each other
            alice_agent = mock_agents["Alice"]
            bob_agent = mock_agents["Bob"]

            self.assertIn("Bob", alice_agent.known_roles)
            self.assertEqual(alice_agent.known_roles["Bob"], Role.WEREWOLF)
            self.assertIn("Alice", bob_agent.known_roles)
            self.assertEqual(bob_agent.known_roles["Alice"], Role.WEREWOLF)
        finally:
            shutil.rmtree(temp_dir)


class TestOrchestratorLogging(unittest.TestCase):
    """Test orchestrator logging functionality"""

    @patch("werewolf.orchestrator.WerewolfGame")
    @patch("werewolf.orchestrator.create_agent")
    def test_log_file_creation(self, mock_create_agent, mock_game):
        """Test that log file is created"""
        mock_game_instance = Mock()
        mock_game.return_value = mock_game_instance
        mock_game_instance.player_names = [
            "Alice",
            "Bob",
            "Charlie",
            "David",
            "Eve",
            "Frank",
        ]
        mock_game_instance.state.roles = {
            "Alice": Role.VILLAGER,
            "Bob": Role.WEREWOLF,
            "Charlie": Role.WEREWOLF,
            "David": Role.SEER,
            "Eve": Role.WITCH,
            "Frank": Role.VILLAGER,
        }

        mock_create_agent.return_value = Mock()

        # Use temporary directory
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "test_game.txt")

        try:
            players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
            orchestrator = WerewolfGameOrchestrator(
                players, "test_model", game_type="six", verbose=False, log_file=log_file
            )

            # Check log file exists
            self.assertTrue(os.path.exists(log_file))

            # Check log file has header
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("WEREWOLF GAME", content)
            self.assertIn("COMPLETE TRANSCRIPT", content)

        finally:
            shutil.rmtree(temp_dir)

    @patch("werewolf.orchestrator.WerewolfGame")
    @patch("werewolf.orchestrator.create_agent")
    def test_log_write_on_message(self, mock_create_agent, mock_game):
        """Test that _log writes to file"""
        mock_game_instance = Mock()
        mock_game.return_value = mock_game_instance
        mock_game_instance.player_names = [
            "Alice",
            "Bob",
            "Charlie",
            "David",
            "Eve",
            "Frank",
        ]
        mock_game_instance.state.roles = {
            "Alice": Role.VILLAGER,
            "Bob": Role.WEREWOLF,
            "Charlie": Role.WEREWOLF,
            "David": Role.SEER,
            "Eve": Role.WITCH,
            "Frank": Role.VILLAGER,
        }

        mock_create_agent.return_value = Mock()

        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "test_game.txt")

        try:
            players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
            orchestrator = WerewolfGameOrchestrator(
                players, "test_model", game_type="six", verbose=False, log_file=log_file
            )

            # Write a test message
            test_message = "TEST MESSAGE FOR LOGGING"
            orchestrator._log(test_message)

            # Check message is in file
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(test_message, content)

        finally:
            shutil.rmtree(temp_dir)


class TestOrchestratorStrategyLoading(unittest.TestCase):
    """Test strategy loading and application"""

    @patch("werewolf.orchestrator.StrategyManager")
    @patch("werewolf.orchestrator.WerewolfGame")
    @patch("werewolf.orchestrator.create_agent")
    def test_strategies_loaded_on_init(
        self, mock_create_agent, mock_game, mock_sm_class
    ):
        """Test that strategies are loaded when creating agents"""
        mock_game_instance = Mock()
        mock_game.return_value = mock_game_instance
        mock_game_instance.player_names = ["Alice", "Bob"]
        mock_game_instance.state.roles = {
            "Alice": Role.VILLAGER,
            "Bob": Role.WEREWOLF,
        }

        # Mock strategy manager - ensure it doesn't create real directories
        mock_sm = Mock()
        mock_sm_class.return_value = mock_sm
        mock_sm.root = tempfile.mkdtemp()  # Use temp directory
        mock_sm.load_rules_for_role.return_value = ["Rule 1", "Rule 2"]

        mock_create_agent.return_value = Mock()

        # Use temporary log file
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "test_game.txt")

        try:
            players = ["Alice", "Bob"]
            orchestrator = WerewolfGameOrchestrator(
                players, "test_model", game_type="six", verbose=False, log_file=log_file
            )

            # Check that strategies were loaded for each role
            self.assertTrue(mock_sm.load_rules_for_role.called)
            # Should load for villager and werewolf
            calls = mock_sm.load_rules_for_role.call_args_list
            loaded_roles = [call[0][0] for call in calls]
            self.assertIn("villager", loaded_roles)
            self.assertIn("werewolf", loaded_roles)
        finally:
            shutil.rmtree(temp_dir)

    @patch("werewolf.orchestrator.StrategyManager")
    @patch("werewolf.orchestrator.WerewolfGame")
    @patch("werewolf.orchestrator.create_agent")
    def test_strategies_passed_to_agents(
        self, mock_create_agent, mock_game, mock_sm_class
    ):
        """Test that loaded strategies are passed to create_agent"""
        mock_game_instance = Mock()
        mock_game.return_value = mock_game_instance
        mock_game_instance.player_names = ["Alice"]
        mock_game_instance.state.roles = {"Alice": Role.SEER}

        # Mock strategy manager with specific rules
        mock_sm = Mock()
        mock_sm_class.return_value = mock_sm
        test_rules = ["Seer Rule 1", "Seer Rule 2"]
        mock_sm.load_rules_for_role.return_value = test_rules

        mock_create_agent.return_value = Mock()

        # Use temporary log file
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "test_game.txt")

        try:
            players = ["Alice"]
            orchestrator = WerewolfGameOrchestrator(
                players, "test_model", game_type="six", verbose=False, log_file=log_file
            )

            # Check that create_agent was called with strategy_rules
            mock_create_agent.assert_called_once()
            call_kwargs = mock_create_agent.call_args[1]
            self.assertIn("strategy_rules", call_kwargs)
            self.assertEqual(call_kwargs["strategy_rules"], test_rules)
        finally:
            shutil.rmtree(temp_dir)


class TestOrchestratorNightPhase(unittest.TestCase):
    """Test night phase execution order and logging"""

    def _create_mock_orchestrator(self):
        """Helper to create a mock orchestrator with agents"""
        with (
            patch("werewolf.orchestrator.WerewolfGame") as mock_game,
            patch("werewolf.orchestrator.create_agent") as mock_create_agent,
        ):

            mock_game_instance = Mock()
            mock_game.return_value = mock_game_instance
            mock_game_instance.player_names = [
                "Alice",
                "Bob",
                "Charlie",
                "David",
                "Eve",
                "Frank",
            ]
            mock_game_instance.state.roles = {
                "Alice": Role.GUARDIAN,
                "Bob": Role.WEREWOLF,
                "Charlie": Role.WEREWOLF,
                "David": Role.SEER,
                "Eve": Role.WITCH,
                "Frank": Role.VILLAGER,
            }
            mock_game_instance.state.alive_players = [
                "Alice",
                "Bob",
                "Charlie",
                "David",
                "Eve",
                "Frank",
            ]
            mock_game_instance.state.game_log = []  # Make it a real list for slicing
            mock_game_instance.state.death_records = []
            mock_game_instance.execute_night_phase.return_value = {
                "werewolf_target": "Frank",
                "seer_checks": {"David": Role.WEREWOLF},
            }

            def create_mock_agent(name, role, model, strategy_rules=None):
                agent = Mock()
                agent.name = name
                agent.role = role
                agent.is_alive = True
                agent.known_roles = {}
                return agent

            mock_create_agent.side_effect = create_mock_agent

            # Use temporary log file
            temp_dir = tempfile.mkdtemp()
            log_file = os.path.join(temp_dir, "test_game.txt")

            orchestrator = WerewolfGameOrchestrator(
                ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"],
                "test_model",
                game_type="six",
                verbose=False,
                log_file=log_file,
            )

            return orchestrator, mock_game_instance, temp_dir

    def test_night_phase_execution_order(self):
        """Test that night phase executes in correct order: Guardian -> Werewolf -> Seer -> Witch"""
        orchestrator, mock_game, temp_dir = self._create_mock_orchestrator()

        try:
            # Track order of logs
            log_order = []
            original_log = orchestrator._log

            def track_log(msg):
                if "[GUARDIAN]" in msg:
                    log_order.append("guardian")
                elif "[WEREWOLVES]" in msg:
                    log_order.append("werewolves")
                elif "[SEER]" in msg:
                    log_order.append("seer")
                elif "[WITCH]" in msg:
                    log_order.append("witch")
                original_log(msg)

            orchestrator._log = track_log
            orchestrator._run_night_phase()

            # Check order
            self.assertEqual(log_order.index("guardian"), 0)
            self.assertEqual(log_order.index("werewolves"), 1)
            self.assertEqual(log_order.index("seer"), 2)
            self.assertEqual(log_order.index("witch"), 3)
        finally:
            shutil.rmtree(temp_dir)

    def test_seer_check_logs_team(self):
        """Test that seer check result logs show team (好人/坏人) not specific role"""
        orchestrator, mock_game, temp_dir = self._create_mock_orchestrator()

        try:
            # Mock seer check returning werewolf
            mock_game.execute_night_phase.return_value = {
                "seer_checks": {"David": Role.WEREWOLF},
                "werewolf_target": None,
            }

            # Capture logs
            logged_messages = []
            original_log = orchestrator._log
            orchestrator._log = lambda msg: logged_messages.append(msg)

            orchestrator._run_night_phase()

            # Find seer log
            seer_logs = [msg for msg in logged_messages if "David learned" in msg]
            self.assertTrue(len(seer_logs) > 0)

            # Should show "坏人" not "werewolf"
            seer_log = seer_logs[0]
            self.assertIn("坏人", seer_log)
            self.assertNotIn("werewolf", seer_log.lower())
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
