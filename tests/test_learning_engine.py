"""
Unit tests for learning engine components

Tests for ReviewAgent, CriticAgent, StrategyManager, and learning pipeline
"""

import unittest
import os
import json
import shutil
import tempfile
import glob
from unittest.mock import Mock, patch

from werewolf.learning_engine import (
    ReviewAgent,
    CriticAgent,
    StrategyManager,
    run_learning_pipeline,
)
from werewolf.werewolf_game import Role


class TestStrategyManager(unittest.TestCase):
    """Tests for StrategyManager strategy persistence and backup"""

    def setUp(self):
        """Create temporary directory for test strategies"""
        self.test_dir = tempfile.mkdtemp()
        self.sm = StrategyManager(root=self.test_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_and_load_rules(self):
        """Test basic save and load functionality"""
        rules = ["Rule 1: Check suspicious players", "Rule 2: Vote with majority"]
        self.sm.save_rules_for_role("villager", rules)

        loaded_rules = self.sm.load_rules_for_role("villager")
        self.assertEqual(loaded_rules, rules)

    def test_load_nonexistent_role(self):
        """Test loading rules for a role that doesn't exist"""
        rules = self.sm.load_rules_for_role("nonexistent")
        self.assertEqual(rules, [])

    def test_deduplication(self):
        """Test that duplicate rules are removed"""
        rules = ["Rule 1", "Rule 2", "Rule 1", "Rule 3", "Rule 2"]
        self.sm.save_rules_for_role("test_role", rules)

        loaded_rules = self.sm.load_rules_for_role("test_role")
        # Should keep only unique rules in order of first appearance
        self.assertEqual(len(loaded_rules), 3)
        self.assertIn("Rule 1", loaded_rules)
        self.assertIn("Rule 2", loaded_rules)
        self.assertIn("Rule 3", loaded_rules)

    def test_empty_rules_filtered(self):
        """Test that empty/whitespace rules are filtered out"""
        rules = ["Rule 1", "", "  ", "Rule 2", "\t", "Rule 3"]
        self.sm.save_rules_for_role("test_role", rules)

        loaded_rules = self.sm.load_rules_for_role("test_role")
        self.assertEqual(len(loaded_rules), 3)
        self.assertEqual(loaded_rules, ["Rule 1", "Rule 2", "Rule 3"])

    def test_backup_on_update(self):
        """Test that backup is created when updating existing strategy"""
        # First save
        initial_rules = ["Initial Rule 1", "Initial Rule 2"]
        self.sm.save_rules_for_role("werewolf", initial_rules)

        # Verify file exists
        strategy_file = self.sm._file_for_role("werewolf")
        self.assertTrue(os.path.exists(strategy_file))

        # Update (should create backup)
        updated_rules = ["Updated Rule 1", "Updated Rule 2", "Updated Rule 3"]
        self.sm.save_rules_for_role("werewolf", updated_rules)

        # Check backup was created
        backups = glob.glob(os.path.join(self.sm.backup_root, "werewolf_*.json"))
        self.assertEqual(len(backups), 1)

        # Verify backup contains old rules
        with open(backups[0], "r", encoding="utf-8") as f:
            backup_data = json.load(f)
        self.assertEqual(backup_data["rules"], initial_rules)

        # Verify current file has new rules
        current_rules = self.sm.load_rules_for_role("werewolf")
        self.assertEqual(current_rules, updated_rules)

    def test_multiple_backups(self):
        """Test that multiple updates create multiple backups"""
        # First save
        self.sm.save_rules_for_role("seer", ["Version 1"])

        # Update multiple times
        self.sm.save_rules_for_role("seer", ["Version 2"])
        self.sm.save_rules_for_role("seer", ["Version 3"])
        self.sm.save_rules_for_role("seer", ["Version 4"])

        # Check backups
        backups = sorted(glob.glob(os.path.join(self.sm.backup_root, "seer_*.json")))
        self.assertEqual(len(backups), 3)  # 3 backups for versions 1, 2, 3

        # Current should be version 4
        current = self.sm.load_rules_for_role("seer")
        self.assertEqual(current, ["Version 4"])

    def test_backup_filename_format(self):
        """Test that backup filenames include timestamp"""
        self.sm.save_rules_for_role("witch", ["Rule 1"])
        self.sm.save_rules_for_role("witch", ["Rule 2"])

        backups = glob.glob(os.path.join(self.sm.backup_root, "witch_*.json"))
        self.assertEqual(len(backups), 1)

        # Check filename format: witch_YYYYMMDD_HHMMSS_microseconds.json
        backup_name = os.path.basename(backups[0])
        self.assertTrue(backup_name.startswith("witch_"))
        self.assertTrue(backup_name.endswith(".json"))
        # Extract timestamp part (now includes microseconds)
        timestamp = backup_name[6:-5]  # Remove "witch_" and ".json"
        self.assertGreaterEqual(len(timestamp), 15)  # At least YYYYMMDD_HHMMSS

    def test_updated_at_timestamp(self):
        """Test that strategy files include updated_at timestamp"""
        self.sm.save_rules_for_role("hunter", ["Rule 1"])

        strategy_file = self.sm._file_for_role("hunter")
        with open(strategy_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("updated_at", data)
        self.assertIn("rules", data)
        # Check timestamp format (ISO format)
        self.assertIn("T", data["updated_at"])

    def test_backup_directory_created(self):
        """Test that backup directory is created automatically"""
        # Create new StrategyManager with fresh directory
        new_dir = tempfile.mkdtemp()
        try:
            new_sm = StrategyManager(root=new_dir)
            # Backup directory should be created in __init__
            self.assertTrue(os.path.exists(new_sm.backup_root))
        finally:
            shutil.rmtree(new_dir)

    def test_apply_to_agents(self):
        """Test applying strategies to agents"""
        # Save some strategies
        self.sm.save_rules_for_role("villager", ["Villager Rule 1", "Villager Rule 2"])
        self.sm.save_rules_for_role("werewolf", ["Werewolf Rule 1"])

        # Create mock agents
        mock_villager = Mock()
        mock_villager.set_strategy_rules = Mock()
        mock_werewolf = Mock()
        mock_werewolf.set_strategy_rules = Mock()

        agents = {"Alice": mock_villager, "Bob": mock_werewolf}
        roles = {"Alice": Role.VILLAGER, "Bob": Role.WEREWOLF}

        # Apply strategies
        self.sm.apply_to_agents(agents, roles)

        # Verify set_strategy_rules was called with correct rules
        mock_villager.set_strategy_rules.assert_called_once()
        villager_rules = mock_villager.set_strategy_rules.call_args[0][0]
        self.assertEqual(villager_rules, ["Villager Rule 1", "Villager Rule 2"])

        mock_werewolf.set_strategy_rules.assert_called_once()
        werewolf_rules = mock_werewolf.set_strategy_rules.call_args[0][0]
        self.assertEqual(werewolf_rules, ["Werewolf Rule 1"])

    def test_corrupted_file_handling(self):
        """Test handling of corrupted strategy files"""
        # Create corrupted JSON file
        strategy_file = self.sm._file_for_role("corrupted")
        os.makedirs(os.path.dirname(strategy_file), exist_ok=True)
        with open(strategy_file, "w") as f:
            f.write("{ invalid json }")

        # Should return empty list on error
        rules = self.sm.load_rules_for_role("corrupted")
        self.assertEqual(rules, [])


class TestReviewAgent(unittest.TestCase):
    """Tests for ReviewAgent (basic structure tests)"""

    def test_review_agent_creation(self):
        """Test that ReviewAgent can be created with a model"""
        mock_model = Mock()
        agent = ReviewAgent(mock_model)
        self.assertIsNotNone(agent)
        self.assertEqual(agent.model, mock_model)


class TestCriticAgent(unittest.TestCase):
    """Tests for CriticAgent (basic structure tests)"""

    def test_critic_agent_creation(self):
        """Test that CriticAgent can be created with a model"""
        mock_model = Mock()
        agent = CriticAgent(mock_model)
        self.assertIsNotNone(agent)
        self.assertEqual(agent.model, mock_model)


if __name__ == "__main__":
    unittest.main()
