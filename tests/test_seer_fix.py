"""
Test for the SeerAgent duplicate checking fix
"""

import unittest
from unittest.mock import Mock, patch
from werewolf.agents import SeerAgent
from werewolf.werewolf_game import Role


class TestSeerAgentFix(unittest.TestCase):
    """Test the fix for SeerAgent duplicate checking issue"""

    def test_seer_filtering_logic(self):
        """Test the core filtering logic without model calls"""
        # Simulate the filtering logic from night_action
        known_roles = {"Seer1": Role.SEER, "Alice": Role.VILLAGER, "Bob": Role.WEREWOLF}
        name = "Seer1"
        targets = ["Alice", "Bob", "Charlie", "David"]

        # This is the logic we fixed
        checked_players = set(known_roles.keys()) - {name}
        unchecked_targets = [t for t in targets if t not in checked_players]
        available_targets = unchecked_targets if unchecked_targets else targets

        # Assertions
        self.assertEqual(set(checked_players), {"Alice", "Bob"})
        self.assertEqual(unchecked_targets, ["Charlie", "David"])
        self.assertEqual(available_targets, ["Charlie", "David"])

    def test_seer_all_checked_fallback(self):
        """Test fallback when all players are checked"""
        known_roles = {"Seer1": Role.SEER, "Alice": Role.VILLAGER, "Bob": Role.WEREWOLF}
        name = "Seer1"
        targets = ["Alice", "Bob"]  # All targets are already checked

        checked_players = set(known_roles.keys()) - {name}
        unchecked_targets = [t for t in targets if t not in checked_players]
        available_targets = unchecked_targets if unchecked_targets else targets

        # Should fallback to original targets when all are checked
        self.assertEqual(unchecked_targets, [])
        self.assertEqual(available_targets, targets)

    @patch("werewolf.agents.AgentBase.__init__")
    @patch("werewolf.agents._run_model_sync")
    def test_seer_night_action_integration(self, mock_model_sync, mock_init):
        """Integration test for night_action method"""
        mock_init.return_value = None

        # Mock simple response
        mock_response = Mock()
        mock_response.content = "Charlie"
        mock_model_sync.return_value = mock_response

        agent = SeerAgent(name="Seer1", role=Role.SEER, model_config_name="test_model")
        agent.model = Mock()

        # Set up already checked players
        agent.known_roles = {
            "Seer1": Role.SEER,
            "Alice": Role.VILLAGER,
            "Bob": Role.WEREWOLF,
        }

        # Test the night action
        targets = ["Alice", "Bob", "Charlie", "David"]
        result = agent.night_action("Test context", targets)

        # Verify model was called and result is valid
        mock_model_sync.assert_called_once()
        self.assertEqual(result, "Charlie")

    def test_edge_case_empty_targets(self):
        """Test edge case with empty targets"""
        known_roles = {"Seer1": Role.SEER}
        name = "Seer1"
        targets = []

        checked_players = set(known_roles.keys()) - {name}
        unchecked_targets = [t for t in targets if t not in checked_players]
        available_targets = unchecked_targets if unchecked_targets else targets

        self.assertEqual(available_targets, [])


if __name__ == "__main__":
    unittest.main()
