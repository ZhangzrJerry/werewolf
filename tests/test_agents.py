"""
Unit tests for Werewolf AI Agents
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from werewolf.agents import (
    VillagerAgent,
    WerewolfAgent,
    SeerAgent,
    WitchAgent,
    GuardianAgent,
    create_agent,
)
from werewolf.werewolf_game import Role


class TestAgentCreation(unittest.TestCase):
    """Test agent creation and initialization"""

    @patch("werewolf.agents.AgentBase.__init__")
    def test_create_villager_agent(self, mock_init):
        """Test creating a villager agent"""
        mock_init.return_value = None

        agent = VillagerAgent(
            name="TestVillager", role=Role.VILLAGER, model_config_name="test_model"
        )

        self.assertEqual(agent.role, Role.VILLAGER)
        self.assertTrue(agent.is_alive)
        self.assertIn("TestVillager", agent.known_roles)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_create_werewolf_agent(self, mock_init):
        """Test creating a werewolf agent"""
        mock_init.return_value = None

        agent = WerewolfAgent(
            name="TestWerewolf", role=Role.WEREWOLF, model_config_name="test_model"
        )

        self.assertEqual(agent.role, Role.WEREWOLF)
        self.assertTrue(agent.is_alive)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_create_seer_agent(self, mock_init):
        """Test creating a seer agent"""
        mock_init.return_value = None

        agent = SeerAgent(
            name="TestSeer", role=Role.SEER, model_config_name="test_model"
        )

        self.assertEqual(agent.role, Role.SEER)
        self.assertTrue(agent.is_alive)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_create_witch_agent(self, mock_init):
        """Test creating a witch agent"""
        mock_init.return_value = None

        agent = WitchAgent(
            name="TestWitch", role=Role.WITCH, model_config_name="test_model"
        )

        self.assertEqual(agent.role, Role.WITCH)
        self.assertFalse(agent.antidote_used)
        self.assertFalse(agent.poison_used)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_create_guardian_agent(self, mock_init):
        """Test creating a guardian agent"""
        mock_init.return_value = None

        agent = GuardianAgent(
            name="TestGuardian", role=Role.GUARDIAN, model_config_name="test_model"
        )

        self.assertEqual(agent.role, Role.GUARDIAN)
        self.assertIsNone(agent.last_protected)


class TestAgentMemory(unittest.TestCase):
    """Test agent memory and state management"""

    @patch("werewolf.agents.AgentBase.__init__")
    def test_update_game_state(self, mock_init):
        """Test updating agent's game state"""
        mock_init.return_value = None

        agent = VillagerAgent(
            name="TestAgent", role=Role.VILLAGER, model_config_name="test_model"
        )

        game_state = {"day_count": 1, "alive_players": ["Alice", "Bob"], "phase": "day"}

        agent.update_game_state(game_state)

        self.assertEqual(len(agent.memory_history), 1)
        self.assertEqual(agent.memory_history[0]["type"], "game_state_update")
        self.assertEqual(agent.memory_history[0]["state"]["day_count"], 1)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_receive_information(self, mock_init):
        """Test agent receiving information"""
        mock_init.return_value = None

        agent = SeerAgent(
            name="TestSeer", role=Role.SEER, model_config_name="test_model"
        )

        info = {"checked_player": "Bob", "result": Role.WEREWOLF}

        agent.receive_information(info)

        self.assertEqual(len(agent.memory_history), 1)
        self.assertEqual(agent.memory_history[0]["type"], "information")

    @patch("werewolf.agents.AgentBase.__init__")
    def test_mark_dead(self, mock_init):
        """Test marking agent as dead"""
        mock_init.return_value = None

        agent = VillagerAgent(
            name="TestAgent", role=Role.VILLAGER, model_config_name="test_model"
        )

        self.assertTrue(agent.is_alive)
        agent.mark_dead()
        self.assertFalse(agent.is_alive)


class TestSeerAgent(unittest.TestCase):
    """Test Seer agent specific functionality"""

    @patch("werewolf.agents.AgentBase.__init__")
    def test_seer_knows_checked_roles(self, mock_init):
        """Test that seer remembers checked roles"""
        mock_init.return_value = None

        agent = SeerAgent(name="Seer1", role=Role.SEER, model_config_name="test_model")

        # Initially only knows own role
        self.assertEqual(len(agent.known_roles), 1)

        # Add checked role
        agent.known_roles["Bob"] = Role.WEREWOLF

        self.assertEqual(len(agent.known_roles), 2)
        self.assertEqual(agent.known_roles["Bob"], Role.WEREWOLF)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_seer_filters_already_checked_players(self, mock_init):
        """Test that seer doesn't re-check already checked players"""
        mock_init.return_value = None

        agent = SeerAgent(name="Seer1", role=Role.SEER, model_config_name="test_model")

        # Set up known roles (seer has already checked Alice and Bob)
        agent.known_roles = {
            "Seer1": Role.SEER,
            "Alice": Role.VILLAGER,
            "Bob": Role.WEREWOLF,
        }

        # Available targets include already checked players
        targets = ["Alice", "Bob", "Charlie", "David"]

        # Filter logic from the fixed night_action method
        checked_players = set(agent.known_roles.keys()) - {agent.name}
        unchecked_targets = [t for t in targets if t not in checked_players]

        # Verify filtering works correctly
        self.assertEqual(set(checked_players), {"Alice", "Bob"})
        self.assertEqual(unchecked_targets, ["Charlie", "David"])
        self.assertNotIn("Alice", unchecked_targets)
        self.assertNotIn("Bob", unchecked_targets)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_seer_fallback_when_all_checked(self, mock_init):
        """Test seer fallback behavior when all players are checked"""
        mock_init.return_value = None

        agent = SeerAgent(name="Seer1", role=Role.SEER, model_config_name="test_model")

        # All players have been checked
        agent.known_roles = {
            "Seer1": Role.SEER,
            "Alice": Role.VILLAGER,
            "Bob": Role.WEREWOLF,
            "Charlie": Role.VILLAGER,
        }

        targets = ["Alice", "Bob", "Charlie"]

        # Filter logic
        checked_players = set(agent.known_roles.keys()) - {agent.name}
        unchecked_targets = [t for t in targets if t not in checked_players]
        available_targets = unchecked_targets if unchecked_targets else targets

        # When all are checked, should fallback to original targets
        self.assertEqual(unchecked_targets, [])
        self.assertEqual(available_targets, targets)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_seer_empty_targets_handling(self, mock_init):
        """Test seer behavior with empty target list"""
        mock_init.return_value = None

        agent = SeerAgent(name="Seer1", role=Role.SEER, model_config_name="test_model")

        targets = []
        checked_players = set(agent.known_roles.keys()) - {agent.name}
        unchecked_targets = [t for t in targets if t not in checked_players]
        available_targets = unchecked_targets if unchecked_targets else targets

        # Should handle empty targets gracefully
        self.assertEqual(available_targets, [])

    @patch("werewolf.agents._run_model_sync")
    @patch("werewolf.agents.AgentBase.__init__")
    def test_seer_night_action_avoids_rechecking(self, mock_init, mock_model_sync):
        """Test that seer's night_action method correctly filters already checked players"""
        mock_init.return_value = None

        # Mock model response to choose Charlie
        mock_response = Mock()
        mock_response.content = "I choose Charlie"
        mock_model_sync.return_value = mock_response

        agent = SeerAgent(name="Seer1", role=Role.SEER, model_config_name="test_model")
        agent.model = Mock()

        # Set up scenario where Alice and Bob are already checked
        agent.known_roles = {
            "Seer1": Role.SEER,
            "Alice": Role.VILLAGER,
            "Bob": Role.WEREWOLF,
        }

        # Call night_action with targets including already checked players
        all_targets = ["Alice", "Bob", "Charlie", "David"]
        context = "Test context"

        result = agent.night_action(context, all_targets)

        # Verify that the model was called with filtered targets (excluding Alice and Bob)
        mock_model_sync.assert_called_once()
        call_args = mock_model_sync.call_args[0]
        prompt = call_args[0][0].content

        # The prompt should mention available targets excluding already checked players
        self.assertIn("Charlie", prompt)
        self.assertIn("David", prompt)
        self.assertIn("You've already checked: Alice, Bob", prompt)

        # Should return Charlie as that's what the model chose
        self.assertEqual(result, "Charlie")

    @patch("werewolf.agents._run_model_sync")
    @patch("werewolf.agents.AgentBase.__init__")
    def test_seer_night_action_fallback_all_checked(self, mock_init, mock_model_sync):
        """Test seer night_action fallback when all players are already checked"""
        mock_init.return_value = None

        # Mock model response
        mock_response = Mock()
        mock_response.content = "I choose Alice again"
        mock_model_sync.return_value = mock_response

        agent = SeerAgent(name="Seer1", role=Role.SEER, model_config_name="test_model")
        agent.model = Mock()

        # All players already checked
        agent.known_roles = {
            "Seer1": Role.SEER,
            "Alice": Role.VILLAGER,
            "Bob": Role.WEREWOLF,
        }

        targets = ["Alice", "Bob"]
        context = "All players checked scenario"

        result = agent.night_action(context, targets)

        # Should allow re-checking when no unchecked players remain
        mock_model_sync.assert_called_once()
        call_args = mock_model_sync.call_args[0]
        prompt = call_args[0][0].content

        # Should show original targets since all are checked
        self.assertIn("Alice", prompt)
        self.assertIn("Bob", prompt)

        self.assertEqual(result, "Alice")


class TestWitchAgent(unittest.TestCase):
    """Test Witch agent specific functionality"""

    @patch("werewolf.agents.AgentBase.__init__")
    def test_witch_ability_usage(self, mock_init):
        """Test witch ability usage tracking"""
        mock_init.return_value = None

        agent = WitchAgent(
            name="Witch1", role=Role.WITCH, model_config_name="test_model"
        )

        # Initially both abilities available
        self.assertFalse(agent.antidote_used)
        self.assertFalse(agent.poison_used)

        # Use antidote
        agent.antidote_used = True
        self.assertTrue(agent.antidote_used)
        self.assertFalse(agent.poison_used)

        # Use poison
        agent.poison_used = True
        self.assertTrue(agent.antidote_used)
        self.assertTrue(agent.poison_used)


class TestGuardianAgent(unittest.TestCase):
    """Test Guardian agent specific functionality"""

    @patch("werewolf.agents.AgentBase.__init__")
    def test_guardian_protection_tracking(self, mock_init):
        """Test guardian tracks last protected player"""
        mock_init.return_value = None

        agent = GuardianAgent(
            name="Guardian1", role=Role.GUARDIAN, model_config_name="test_model"
        )

        # Initially no one protected
        self.assertIsNone(agent.last_protected)

        # Protect Alice
        agent.last_protected = "Alice"
        self.assertEqual(agent.last_protected, "Alice")

        # Protect Bob (different player)
        agent.last_protected = "Bob"
        self.assertEqual(agent.last_protected, "Bob")


class TestAgentFactory(unittest.TestCase):
    """Test agent factory function"""

    @patch("werewolf.agents.VillagerAgent.__init__")
    @patch("werewolf.agents.WerewolfAgent.__init__")
    @patch("werewolf.agents.SeerAgent.__init__")
    def test_create_agent_factory(self, mock_seer, mock_wolf, mock_villager):
        """Test that factory creates correct agent types"""
        mock_villager.return_value = None
        mock_wolf.return_value = None
        mock_seer.return_value = None

        # Create villager
        agent = create_agent("Alice", Role.VILLAGER, "test_model")
        self.assertIsInstance(agent, VillagerAgent)

        # Create werewolf
        agent = create_agent("Bob", Role.WEREWOLF, "test_model")
        self.assertIsInstance(agent, WerewolfAgent)

        # Create seer
        agent = create_agent("Charlie", Role.SEER, "test_model")
        self.assertIsInstance(agent, SeerAgent)


class TestSystemPrompts(unittest.TestCase):
    """Test that agents have appropriate system prompts"""

    @patch("werewolf.agents.AgentBase.__init__")
    def test_villager_prompt_content(self, mock_init):
        """Test villager system prompt contains key concepts"""
        mock_init.return_value = None

        agent = VillagerAgent(
            name="TestVillager", role=Role.VILLAGER, model_config_name="test_model"
        )

        prompt = agent._get_default_sys_prompt()

        # Check key concepts are in prompt
        self.assertIn("VILLAGER", prompt.upper())
        self.assertIn("good side", prompt.lower())
        self.assertIn("werewolves", prompt.lower())

    @patch("werewolf.agents.AgentBase.__init__")
    def test_werewolf_prompt_deception(self, mock_init):
        """Test werewolf prompt emphasizes deception"""
        mock_init.return_value = None

        agent = WerewolfAgent(
            name="TestWerewolf", role=Role.WEREWOLF, model_config_name="test_model"
        )

        prompt = agent._get_default_sys_prompt()

        # Check deception strategy is emphasized
        self.assertIn("WEREWOLF", prompt.upper())
        self.assertIn("pretend", prompt.lower() or "deception" in prompt.lower())
        self.assertIn("blend", prompt.lower() or "hide" in prompt.lower())

    @patch("werewolf.agents.AgentBase.__init__")
    def test_seer_prompt_strategy(self, mock_init):
        """Test seer prompt includes strategic information sharing"""
        mock_init.return_value = None

        agent = SeerAgent(
            name="TestSeer", role=Role.SEER, model_config_name="test_model"
        )

        prompt = agent._get_default_sys_prompt()

        # Check strategic elements
        self.assertIn("SEER", prompt.upper())
        self.assertIn("check", prompt.lower())
        self.assertIn("information", prompt.lower())


class TestHunterAgent(unittest.TestCase):
    """Test Hunter agent specific functionality"""

    @patch("werewolf.agents.AgentBase.__init__")
    def test_hunter_creation(self, mock_init):
        """Test creating a hunter agent"""
        from werewolf.agents import HunterAgent

        mock_init.return_value = None

        agent = HunterAgent(
            name="TestHunter", role=Role.HUNTER, model_config_name="test_model"
        )

        self.assertEqual(agent.role, Role.HUNTER)
        self.assertTrue(agent.is_alive)

    @patch("werewolf.agents._run_model_sync")
    @patch("werewolf.agents.AgentBase.__init__")
    def test_hunter_shoot_target(self, mock_init, mock_model_sync):
        """Test hunter choosing a target to shoot when dying"""
        from werewolf.agents import HunterAgent

        mock_init.return_value = None

        # Mock model response
        mock_response = Mock()
        mock_response.content = "I choose to shoot Bob"
        mock_model_sync.return_value = mock_response

        agent = HunterAgent(
            name="TestHunter", role=Role.HUNTER, model_config_name="test_model"
        )
        agent.model = Mock()

        alive_players = ["Alice", "Bob", "Charlie"]
        target = agent.shoot_target("Game context", alive_players, "werewolf_kill")

        # Should extract a valid player name
        self.assertIn(target, alive_players)
        mock_model_sync.assert_called_once()

    @patch("werewolf.agents.AgentBase.__init__")
    def test_hunter_prompt_includes_death_cause(self, mock_init):
        """Test that hunter's shoot prompt includes cause of death"""
        from werewolf.agents import HunterAgent

        mock_init.return_value = None

        agent = HunterAgent(
            name="TestHunter", role=Role.HUNTER, model_config_name="test_model"
        )

        # Check system prompt mentions shooting when dying
        prompt = agent._get_default_sys_prompt()
        self.assertIn("HUNTER", prompt.upper())
        self.assertIn("shoot", prompt.lower())
        self.assertIn("die", prompt.lower() or "dying" in prompt.lower())


class TestLastWords(unittest.TestCase):
    """Test last words functionality for all agents"""

    @patch("werewolf.agents._run_model_sync")
    @patch("werewolf.agents.AgentBase.__init__")
    def test_villager_last_words(self, mock_init, mock_model_sync):
        """Test villager generating last words"""
        mock_init.return_value = None

        # Mock model response
        mock_response = Mock()
        mock_response.content = "I believe Bob is the werewolf. Please vote him out!"
        mock_model_sync.return_value = mock_response

        agent = VillagerAgent(
            name="TestVillager", role=Role.VILLAGER, model_config_name="test_model"
        )
        agent.model = Mock()

        last_words = agent.last_words("Game context", "voted_out")

        # Should return some text
        self.assertIsInstance(last_words, str)
        self.assertGreater(len(last_words), 0)
        mock_model_sync.assert_called_once()

    @patch("werewolf.agents._run_model_sync")
    @patch("werewolf.agents.AgentBase.__init__")
    def test_werewolf_last_words(self, mock_init, mock_model_sync):
        """Test werewolf generating last words"""
        mock_init.return_value = None

        mock_response = Mock()
        mock_response.content = "I suspect Charlie might be hiding something!"
        mock_model_sync.return_value = mock_response

        agent = WerewolfAgent(
            name="TestWolf", role=Role.WEREWOLF, model_config_name="test_model"
        )
        agent.model = Mock()

        last_words = agent.last_words("Game context", "werewolf_kill")

        self.assertIsInstance(last_words, str)
        self.assertGreater(len(last_words), 0)

    @patch("werewolf.agents._run_model_sync")
    @patch("werewolf.agents.AgentBase.__init__")
    def test_last_words_includes_context(self, mock_init, mock_model_sync):
        """Test that last words prompt includes game context"""
        mock_init.return_value = None

        mock_response = Mock()
        mock_response.content = "Final statement"
        mock_model_sync.return_value = mock_response

        agent = SeerAgent(
            name="TestSeer", role=Role.SEER, model_config_name="test_model"
        )
        agent.model = Mock()

        context = "Important game context"
        agent.last_words(context, "voted_out")

        # Check that model was called with a prompt containing context
        call_args = mock_model_sync.call_args
        messages = call_args[0][1]  # Second argument is message list
        prompt_content = messages[0].content

        self.assertIn(context, prompt_content)
        self.assertIn("voted_out", prompt_content)


class TestStrategyRules(unittest.TestCase):
    """Test strategy rules functionality"""

    @patch("werewolf.agents.AgentBase.__init__")
    def test_set_strategy_rules(self, mock_init):
        """Test setting strategy rules for an agent"""
        mock_init.return_value = None

        agent = VillagerAgent(
            name="TestVillager", role=Role.VILLAGER, model_config_name="test_model"
        )

        rules = ["Rule 1: Vote with majority", "Rule 2: Trust the seer"]
        agent.set_strategy_rules(rules)

        self.assertEqual(agent.strategy_rules, rules)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_add_strategy_rules(self, mock_init):
        """Test adding strategy rules to existing ones"""
        mock_init.return_value = None

        agent = VillagerAgent(
            name="TestVillager", role=Role.VILLAGER, model_config_name="test_model"
        )

        agent.set_strategy_rules(["Rule 1"])
        agent.add_strategy_rules(["Rule 2", "Rule 3"])

        self.assertEqual(len(agent.strategy_rules), 3)
        self.assertIn("Rule 1", agent.strategy_rules)
        self.assertIn("Rule 2", agent.strategy_rules)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_add_duplicate_rules_filtered(self, mock_init):
        """Test that duplicate rules are not added"""
        mock_init.return_value = None

        agent = VillagerAgent(
            name="TestVillager", role=Role.VILLAGER, model_config_name="test_model"
        )

        agent.set_strategy_rules(["Rule 1", "Rule 2"])
        agent.add_strategy_rules(["Rule 2", "Rule 3"])  # Rule 2 is duplicate

        self.assertEqual(len(agent.strategy_rules), 3)
        # Count occurrences of Rule 2
        count = agent.strategy_rules.count("Rule 2")
        self.assertEqual(count, 1)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_format_strategy_rules(self, mock_init):
        """Test formatting strategy rules for prompts"""
        mock_init.return_value = None

        agent = VillagerAgent(
            name="TestVillager", role=Role.VILLAGER, model_config_name="test_model"
        )

        agent.set_strategy_rules(["Rule 1", "Rule 2"])
        formatted = agent._format_strategy_rules()

        # Should format as bullet points
        self.assertIn("- Rule 1", formatted)
        self.assertIn("- Rule 2", formatted)

    @patch("werewolf.agents.AgentBase.__init__")
    def test_format_empty_rules(self, mock_init):
        """Test formatting empty strategy rules"""
        mock_init.return_value = None

        agent = VillagerAgent(
            name="TestVillager", role=Role.VILLAGER, model_config_name="test_model"
        )

        # No rules set
        formatted = agent._format_strategy_rules()

        self.assertEqual(formatted, "(none)")

    @patch("werewolf.agents._run_model_sync")
    @patch("werewolf.agents.AgentBase.__init__")
    def test_strategy_rules_in_discuss_prompt(self, mock_init, mock_model_sync):
        """Test that strategy rules appear in discuss prompt"""
        mock_init.return_value = None

        mock_response = Mock()
        mock_response.content = "I think Bob is suspicious"
        mock_model_sync.return_value = mock_response

        agent = VillagerAgent(
            name="TestVillager", role=Role.VILLAGER, model_config_name="test_model"
        )
        agent.model = Mock()
        agent.set_strategy_rules(["Always verify claims", "Watch voting patterns"])

        agent.discuss("Game context", [])

        # Check that the prompt contains strategy guidelines
        call_args = mock_model_sync.call_args
        messages = call_args[0][1]
        prompt = messages[0].content

        self.assertIn("Strategy guidelines", prompt)
        self.assertIn("Always verify claims", prompt)
        self.assertIn("Watch voting patterns", prompt)


if __name__ == "__main__":
    unittest.main()
