"""
Unit tests for WerewolfGame class
"""

import unittest
from unittest.mock import patch
from werewolf import WerewolfGame
from werewolf.werewolf_game import Role, GamePhase


class TestWerewolfGameInit(unittest.TestCase):
    """Test WerewolfGame initialization"""

    def test_init_minimum_players(self):
        """Test that game requires at least 4 players"""
        with self.assertRaises(ValueError) as context:
            WerewolfGame(["Alice", "Bob", "Charlie"])
        self.assertIn("at least 4 players", str(context.exception))

    def test_init_valid_six_player_game(self):
        """Test initialization with 6 players"""
        players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        game = WerewolfGame(players, game_type="six")

        self.assertEqual(len(game.state.players), 6)
        self.assertEqual(len(game.state.alive_players), 6)
        self.assertEqual(game.state.phase, GamePhase.NIGHT)
        self.assertEqual(game.state.day_count, 0)
        self.assertFalse(game.state.witch_poison_used)
        self.assertFalse(game.state.witch_antidote_used)

    def test_init_valid_nine_player_game(self):
        """Test initialization with 9 players"""
        players = [f"Player{i}" for i in range(9)]
        game = WerewolfGame(players, game_type="nine")

        self.assertEqual(len(game.state.players), 9)
        self.assertEqual(len(game.state.roles), 9)

    def test_init_twelve_player_game(self):
        """Test initialization with 12 players"""
        players = [f"Player{i}" for i in range(12)]
        game = WerewolfGame(players, game_type="twelve")

        self.assertEqual(len(game.state.players), 12)
        self.assertEqual(len(game.state.roles), 12)


class TestRoleAssignment(unittest.TestCase):
    """Test role assignment logic"""

    def test_six_player_roles(self):
        """Test that 6-player game has correct role distribution"""
        players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        game = WerewolfGame(players, game_type="six")

        roles = list(game.state.roles.values())
        self.assertEqual(roles.count(Role.WEREWOLF), 2)
        self.assertEqual(roles.count(Role.VILLAGER), 2)
        self.assertEqual(roles.count(Role.SEER), 1)
        self.assertEqual(roles.count(Role.WITCH), 1)

    def test_nine_player_roles(self):
        """Test that 9-player game has correct role distribution"""
        players = [f"Player{i}" for i in range(9)]
        game = WerewolfGame(players, game_type="nine")

        roles = list(game.state.roles.values())
        self.assertEqual(roles.count(Role.WEREWOLF), 3)
        self.assertEqual(roles.count(Role.VILLAGER), 3)
        self.assertEqual(roles.count(Role.SEER), 1)
        self.assertEqual(roles.count(Role.WITCH), 1)
        self.assertEqual(roles.count(Role.HUNTER), 1)

    def test_twelve_player_roles(self):
        """Test that 12-player game has correct role distribution"""
        players = [f"Player{i}" for i in range(12)]
        game = WerewolfGame(players, game_type="twelve")

        roles = list(game.state.roles.values())
        self.assertEqual(roles.count(Role.WEREWOLF), 4)
        self.assertEqual(roles.count(Role.VILLAGER), 4)
        self.assertEqual(roles.count(Role.SEER), 1)
        self.assertEqual(roles.count(Role.WITCH), 1)
        self.assertEqual(roles.count(Role.HUNTER), 1)
        self.assertEqual(roles.count(Role.GUARDIAN), 1)


class TestRoleTeamDetection(unittest.TestCase):
    """Test Role enum team detection methods"""

    def test_werewolf_is_werewolf(self):
        """Test that werewolf role is identified as werewolf"""
        self.assertTrue(Role.WEREWOLF.is_werewolf())

    def test_villager_not_werewolf(self):
        """Test that villager is not werewolf"""
        self.assertFalse(Role.VILLAGER.is_werewolf())

    def test_seer_not_werewolf(self):
        """Test that seer is not werewolf"""
        self.assertFalse(Role.SEER.is_werewolf())

    def test_witch_not_werewolf(self):
        """Test that witch is not werewolf"""
        self.assertFalse(Role.WITCH.is_werewolf())

    def test_hunter_not_werewolf(self):
        """Test that hunter is not werewolf"""
        self.assertFalse(Role.HUNTER.is_werewolf())

    def test_guardian_not_werewolf(self):
        """Test that guardian is not werewolf"""
        self.assertFalse(Role.GUARDIAN.is_werewolf())

    def test_werewolf_team(self):
        """Test that werewolf returns bad team"""
        self.assertEqual(Role.WEREWOLF.get_team(), "坏人")

    def test_villager_team(self):
        """Test that villager returns good team"""
        self.assertEqual(Role.VILLAGER.get_team(), "好人")

    def test_seer_team(self):
        """Test that seer returns good team"""
        self.assertEqual(Role.SEER.get_team(), "好人")

    def test_witch_team(self):
        """Test that witch returns good team"""
        self.assertEqual(Role.WITCH.get_team(), "好人")

    def test_hunter_team(self):
        """Test that hunter returns good team"""
        self.assertEqual(Role.HUNTER.get_team(), "好人")

    def test_guardian_team(self):
        """Test that guardian returns good team"""
        self.assertEqual(Role.GUARDIAN.get_team(), "好人")


class TestNightPhase(unittest.TestCase):
    """Test night phase execution"""

    def setUp(self):
        """Set up a game for testing"""
        self.players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        self.game = WerewolfGame(self.players, game_type="six")

    def test_werewolf_attack_simple(self):
        """Test werewolf attack on a player"""
        # Find werewolves
        werewolves = [p for p, r in self.game.state.roles.items() if r == Role.WEREWOLF]
        victim = [p for p in self.players if p not in werewolves][0]

        # Both werewolves vote for the same victim
        actions = {w: victim for w in werewolves}
        result = self.game.execute_night_phase(actions)

        self.assertEqual(result["werewolf_target"], victim)
        self.assertNotIn(victim, self.game.state.alive_players)

    def test_seer_check(self):
        """Test seer checking a player's role"""
        seer = [p for p, r in self.game.state.roles.items() if r == Role.SEER][0]
        target = [p for p in self.players if p != seer][0]

        actions = {seer: target}
        result = self.game.execute_night_phase(actions)

        self.assertIn("seer_checks", result)
        self.assertIn(seer, result["seer_checks"])
        self.assertEqual(result["seer_checks"][seer], self.game.state.roles[target])

    def test_witch_save(self):
        """Test witch saving the werewolf victim"""
        werewolves = [p for p, r in self.game.state.roles.items() if r == Role.WEREWOLF]
        witch = [p for p, r in self.game.state.roles.items() if r == Role.WITCH][0]
        victim = [p for p in self.players if p not in werewolves and p != witch][0]

        actions = {w: victim for w in werewolves}
        actions[witch] = "save"

        result = self.game.execute_night_phase(actions)

        self.assertEqual(result["werewolf_target"], victim)
        self.assertIn("saved", result)
        self.assertEqual(result["saved"], victim)
        self.assertIn(victim, self.game.state.alive_players)
        self.assertTrue(self.game.state.witch_antidote_used)

    def test_witch_poison(self):
        """Test witch poisoning a player"""
        witch = [p for p, r in self.game.state.roles.items() if r == Role.WITCH][0]
        target = [p for p in self.players if p != witch][0]

        actions = {witch: f"poison:{target}"}
        result = self.game.execute_night_phase(actions)

        self.assertIn("poisoned", result)
        self.assertEqual(result["poisoned"], target)
        self.assertNotIn(target, self.game.state.alive_players)
        self.assertTrue(self.game.state.witch_poison_used)

    def test_witch_single_use_limitation(self):
        """Test that witch can only use each ability once"""
        witch = [p for p, r in self.game.state.roles.items() if r == Role.WITCH][0]
        werewolves = [p for p, r in self.game.state.roles.items() if r == Role.WEREWOLF]
        victim = [p for p in self.players if p not in werewolves and p != witch][0]

        # First night: use antidote
        actions = {w: victim for w in werewolves}
        actions[witch] = "save"
        self.game.execute_night_phase(actions)

        self.assertTrue(self.game.state.witch_antidote_used)

        # Second night: try to use antidote again
        self.game.state.phase = GamePhase.NIGHT
        victim2 = [
            p
            for p in self.game.state.alive_players
            if p not in werewolves and p != witch
        ][0]
        actions = {w: victim2 for w in werewolves}
        actions[witch] = "save"
        result = self.game.execute_night_phase(actions)

        # Victim should die because antidote was already used
        self.assertNotIn(victim2, self.game.state.alive_players)


class TestGuardian(unittest.TestCase):
    """Test Guardian role functionality"""

    def setUp(self):
        """Set up a game with guardian"""
        self.players = [f"Player{i}" for i in range(12)]
        self.game = WerewolfGame(self.players, game_type="twelve")

    def test_guardian_protect(self):
        """Test guardian protecting a player"""
        guardian = [p for p, r in self.game.state.roles.items() if r == Role.GUARDIAN][
            0
        ]
        werewolves = [p for p, r in self.game.state.roles.items() if r == Role.WEREWOLF]
        victim = [p for p in self.players if p not in werewolves and p != guardian][0]

        # Guardian protects the victim
        actions = {w: victim for w in werewolves}
        actions[guardian] = victim

        result = self.game.execute_night_phase(actions)

        self.assertIn("guardian", result)
        self.assertEqual(result["guardian"].get("guarded"), victim)
        self.assertIn(victim, self.game.state.alive_players)

    def test_guardian_cannot_protect_same_player_twice(self):
        """Test that guardian cannot protect the same player consecutively"""
        guardian = [p for p, r in self.game.state.roles.items() if r == Role.GUARDIAN][
            0
        ]
        werewolves = [p for p, r in self.game.state.roles.items() if r == Role.WEREWOLF]
        victim = [p for p in self.players if p not in werewolves and p != guardian][0]

        # First night: protect victim
        actions = {w: victim for w in werewolves}
        actions[guardian] = victim
        self.game.execute_night_phase(actions)

        # Victim should be alive
        self.assertIn(victim, self.game.state.alive_players)

        # Second night: try to protect same victim again
        self.game.state.phase = GamePhase.NIGHT
        actions = {w: victim for w in werewolves}
        actions[guardian] = victim
        self.game.execute_night_phase(actions)

        # Victim should die because guardian cannot protect same player twice
        self.assertNotIn(victim, self.game.state.alive_players)

    def test_guardian_and_witch_both_save(self):
        """Test the rule: if both guardian and witch save the same victim, victim dies"""
        guardian = [p for p, r in self.game.state.roles.items() if r == Role.GUARDIAN][
            0
        ]
        witch = [p for p, r in self.game.state.roles.items() if r == Role.WITCH][0]
        werewolves = [p for p, r in self.game.state.roles.items() if r == Role.WEREWOLF]
        victim = [
            p
            for p in self.players
            if p not in werewolves and p != guardian and p != witch
        ][0]

        # Both guardian and witch try to save the victim
        actions = {w: victim for w in werewolves}
        actions[guardian] = victim
        actions[witch] = "save"

        result = self.game.execute_night_phase(actions)

        # Due to the special rule, victim should die
        self.assertNotIn(victim, self.game.state.alive_players)


class TestDayPhase(unittest.TestCase):
    """Test day phase execution"""

    def setUp(self):
        """Set up a game for testing"""
        self.players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        self.game = WerewolfGame(self.players, game_type="six")

    def test_voting_elimination(self):
        """Test voting to eliminate a player"""
        target = self.players[0]
        # All players vote for the target
        actions = {p: target for p in self.players if p != target}

        result = self.game.execute_day_phase(actions)

        self.assertEqual(result["eliminated"], target)
        self.assertNotIn(target, self.game.state.alive_players)
        self.assertEqual(self.game.state.phase, GamePhase.NIGHT)

    def test_voting_tie_no_elimination(self):
        """Test that ties result in no elimination"""
        # Create a proper tie with equal votes for two different players
        # Players: Alice, Bob, Charlie, David, Eve, Frank
        # Alice, Bob, Charlie vote for David
        # Eve, Frank vote for Alice
        # David doesn't vote or votes for someone else
        actions = {
            "Alice": "David",
            "Bob": "David",
            "Charlie": "David",
            "David": "Alice",
            "Eve": "Alice",
            "Frank": "Alice",
        }

        result = self.game.execute_day_phase(actions)

        # With 3 votes each, it's a tie, so no one should be eliminated
        self.assertEqual(result["eliminated"], "")
        self.assertEqual(len(self.game.state.alive_players), len(self.players))

    def test_day_count_increment(self):
        """Test that day count increments after day phase"""
        initial_day = self.game.state.day_count
        actions = {p: self.players[0] for p in self.players[1:]}

        self.game.execute_day_phase(actions)

        self.assertEqual(self.game.state.day_count, initial_day + 1)


class TestGameEndConditions(unittest.TestCase):
    """Test game end conditions"""

    def setUp(self):
        """Set up a game for testing"""
        self.players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        self.game = WerewolfGame(self.players, game_type="six")

    def test_villagers_win_when_all_werewolves_dead(self):
        """Test that villagers win when all werewolves are eliminated"""
        # Remove all werewolves
        werewolves = [p for p, r in self.game.state.roles.items() if r == Role.WEREWOLF]
        for w in werewolves:
            if w in self.game.state.alive_players:
                self.game.state.alive_players.remove(w)

        ended, winner = self.game.check_game_end()

        self.assertTrue(ended)
        self.assertEqual(winner, "villagers")

    def test_six_player_werewolves_win_condition(self):
        """Test 6-player game: werewolves must kill all civilians AND gods"""
        # In 6-player game, werewolves need to eliminate ALL good players
        werewolves = [p for p, r in self.game.state.roles.items() if r == Role.WEREWOLF]
        villagers = [p for p, r in self.game.state.roles.items() if r != Role.WEREWOLF]

        # Remove all non-werewolves
        for v in villagers:
            if v in self.game.state.alive_players:
                self.game.state.alive_players.remove(v)

        ended, winner = self.game.check_game_end()

        self.assertTrue(ended)
        self.assertEqual(winner, "werewolves")

    def test_nine_player_werewolves_win_all_civilians(self):
        """Test 9-player game: werewolves win when all civilians are eliminated"""
        players = [f"Player{i}" for i in range(9)]
        game = WerewolfGame(players, game_type="nine")

        # Remove all villagers (civilians)
        villagers = [p for p, r in game.state.roles.items() if r == Role.VILLAGER]
        for v in villagers:
            if v in game.state.alive_players:
                game.state.alive_players.remove(v)

        ended, winner = game.check_game_end()

        self.assertTrue(ended)
        self.assertEqual(winner, "werewolves")

    def test_nine_player_werewolves_win_all_gods(self):
        """Test 9-player game: werewolves win when all gods are eliminated"""
        players = [f"Player{i}" for i in range(9)]
        game = WerewolfGame(players, game_type="nine")

        # Remove all gods (seer, witch, hunter)
        gods = [
            p
            for p, r in game.state.roles.items()
            if r in [Role.SEER, Role.WITCH, Role.HUNTER]
        ]
        for g in gods:
            if g in game.state.alive_players:
                game.state.alive_players.remove(g)

        ended, winner = game.check_game_end()

        self.assertTrue(ended)
        self.assertEqual(winner, "werewolves")

    def test_twelve_player_werewolves_win_all_civilians(self):
        """Test 12-player game: werewolves win when all civilians are eliminated"""
        players = [f"Player{i}" for i in range(12)]
        game = WerewolfGame(players, game_type="twelve")

        # Remove all villagers (civilians)
        villagers = [p for p, r in game.state.roles.items() if r == Role.VILLAGER]
        for v in villagers:
            if v in game.state.alive_players:
                game.state.alive_players.remove(v)

        ended, winner = game.check_game_end()

        self.assertTrue(ended)
        self.assertEqual(winner, "werewolves")

    def test_twelve_player_werewolves_win_all_gods(self):
        """Test 12-player game: werewolves win when all gods are eliminated"""
        players = [f"Player{i}" for i in range(12)]
        game = WerewolfGame(players, game_type="twelve")

        # Remove all gods (seer, witch, hunter, guardian)
        gods = [
            p
            for p, r in game.state.roles.items()
            if r in [Role.SEER, Role.WITCH, Role.HUNTER, Role.GUARDIAN]
        ]
        for g in gods:
            if g in game.state.alive_players:
                game.state.alive_players.remove(g)

        ended, winner = game.check_game_end()

        self.assertTrue(ended)
        self.assertEqual(winner, "werewolves")

    def test_game_continues_when_not_ended(self):
        """Test that game continues when end conditions are not met"""
        ended, winner = self.game.check_game_end()

        self.assertFalse(ended)
        self.assertEqual(winner, "")


class TestGameState(unittest.TestCase):
    """Test game state management"""

    def test_to_dict(self):
        """Test converting game state to dictionary"""
        players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        game = WerewolfGame(players, game_type="six")

        state_dict = game.to_dict()

        self.assertIn("players", state_dict)
        self.assertIn("roles", state_dict)
        self.assertIn("alive", state_dict)
        self.assertIn("phase", state_dict)
        self.assertIn("day_count", state_dict)
        self.assertIn("game_log", state_dict)

        self.assertEqual(len(state_dict["players"]), 6)
        self.assertEqual(len(state_dict["roles"]), 6)
        self.assertEqual(state_dict["phase"], "night")

    def test_game_log_recording(self):
        """Test that game actions are recorded in game log"""
        players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        game = WerewolfGame(players, game_type="six")

        # Initial log should have role assignment
        self.assertTrue(len(game.state.game_log) > 0)
        self.assertIn("Roles assigned", game.state.game_log[0])

    def test_death_records_werewolf_kill(self):
        """Test that werewolf kills are recorded in death_records"""
        players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        game = WerewolfGame(players, game_type="six")

        werewolves = [p for p, r in game.state.roles.items() if r == Role.WEREWOLF]
        victim = [p for p in players if p not in werewolves][0]

        # Werewolves attack victim
        actions = {w: victim for w in werewolves}
        game.execute_night_phase(actions)

        # Check death record
        self.assertIn(victim, game.state.death_records)
        self.assertEqual(game.state.death_records[victim], "werewolf_kill")

    def test_death_records_witch_poison(self):
        """Test that witch poison deaths are recorded"""
        players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        game = WerewolfGame(players, game_type="six")

        witch = [p for p, r in game.state.roles.items() if r == Role.WITCH][0]
        target = [p for p in players if p != witch][0]

        # Witch poisons target
        actions = {witch: f"poison:{target}"}
        game.execute_night_phase(actions)

        # Check death record
        self.assertIn(target, game.state.death_records)
        self.assertEqual(game.state.death_records[target], "witch_poison")

    def test_death_records_voted_out(self):
        """Test that voting deaths are recorded"""
        players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        game = WerewolfGame(players, game_type="six")

        target = players[0]
        # All players vote for target
        actions = {p: target for p in players if p != target}
        game.execute_day_phase(actions)

        # Check death record
        self.assertIn(target, game.state.death_records)
        self.assertEqual(game.state.death_records[target], "voted_out")


class TestHunterRole(unittest.TestCase):
    """Test Hunter role functionality"""

    def test_hunter_in_nine_player_game(self):
        """Test that hunter exists in 9-player game"""
        players = [f"Player{i}" for i in range(9)]
        game = WerewolfGame(players, game_type="nine")

        hunter = [p for p, r in game.state.roles.items() if r == Role.HUNTER]
        self.assertEqual(len(hunter), 1)

    def test_hunter_in_twelve_player_game(self):
        """Test that hunter exists in 12-player game"""
        players = [f"Player{i}" for i in range(12)]
        game = WerewolfGame(players, game_type="twelve")

        hunter = [p for p, r in game.state.roles.items() if r == Role.HUNTER]
        self.assertEqual(len(hunter), 1)

    def test_hunter_not_in_six_player_game(self):
        """Test that hunter does not exist in 6-player game"""
        players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        game = WerewolfGame(players, game_type="six")

        hunter = [p for p, r in game.state.roles.items() if r == Role.HUNTER]
        self.assertEqual(len(hunter), 0)


if __name__ == "__main__":
    unittest.main()
