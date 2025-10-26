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


if __name__ == "__main__":
    unittest.main()
