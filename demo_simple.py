"""
Simple example of running a Werewolf game
This is a minimal example without AgentScope to demonstrate the game logic
"""

from werewolf import WerewolfGame, Role


def print_separator():
    print("\n" + "=" * 60 + "\n")


def simple_game_demo():
    """
    Demonstrate game logic without AI agents
    Using predefined actions to show game flow
    """
    print_separator()
    print("🐺 WEREWOLF GAME DEMO (Rule-Based)")
    print_separator()

    # Create game
    players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
    game = WerewolfGame(players, game_type="six")

    print("Players and Roles:")
    for player, role in game.state.roles.items():
        print(f"  {player}: {role.value}")
    print_separator()

    # Round 1 - Night
    print("ROUND 1 - NIGHT PHASE")
    print("-" * 60)

    # Find werewolves
    werewolves = [p for p, r in game.state.roles.items() if r == Role.WEREWOLF]
    print(f"Werewolves: {', '.join(werewolves)}")

    # Werewolves attack
    targets = [p for p in players if p not in werewolves]
    victim = targets[0]  # Attack first non-werewolf

    night_actions = {}
    for wolf in werewolves:
        night_actions[wolf] = victim

    print(f"Werewolves target: {victim}")

    # Seer checks
    seer = [p for p, r in game.state.roles.items() if r == Role.SEER][0]
    check_target = werewolves[0]  # Check first werewolf
    night_actions[seer] = check_target
    print(f"Seer {seer} checks {check_target}")

    # Execute night
    night_result = game.execute_night_phase(night_actions)

    print("\nNight Results:")
    print(f"  Victim: {night_result.get('werewolf_target', 'None')}")
    print(f"  Alive: {', '.join(game.state.alive_players)}")
    print_separator()

    # Check if game ended
    ended, winner = game.check_game_end()
    if ended:
        print(f"Game Over! Winner: {winner}")
        return

    # Round 1 - Day
    print("ROUND 1 - DAY PHASE")
    print("-" * 60)

    print(f"Alive players: {', '.join(game.state.alive_players)}")
    print("\nVoting Phase:")

    # Simple voting: everyone votes for the first werewolf
    day_actions = {}
    for player in game.state.alive_players:
        if werewolves and werewolves[0] in game.state.alive_players:
            day_actions[player] = werewolves[0]

    for voter, target in day_actions.items():
        print(f"  {voter} votes for {target}")

    # Execute day
    day_result = game.execute_day_phase(day_actions)

    eliminated = day_result.get("eliminated")
    if eliminated:
        print(f"\n{eliminated} was eliminated!")
        print(f"Role: {game.state.roles[eliminated].value}")
    else:
        print("\nNo one was eliminated (tie)")

    print(f"Alive: {', '.join(game.state.alive_players)}")
    print_separator()

    # Check if game ended
    ended, winner = game.check_game_end()
    if ended:
        print(f"🏆 GAME OVER! Winner: {winner.upper()}")
        print_separator()
        print("Final Status:")
        for player, role in game.state.roles.items():
            status = "✅ ALIVE" if player in game.state.alive_players else "💀 DEAD"
            print(f"  {player} ({role.value}): {status}")
        print_separator()
    else:
        print("Game continues...")

    return game


def test_special_rules():
    """Test special game rules"""
    print_separator()
    print("🧪 TESTING SPECIAL RULES")
    print_separator()

    # Test witch saving victim
    print("Test 1: Witch saves werewolf victim")
    print("-" * 60)

    players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
    game = WerewolfGame(players, game_type="six")

    werewolves = [p for p, r in game.state.roles.items() if r == Role.WEREWOLF]
    witch = [p for p, r in game.state.roles.items() if r == Role.WITCH][0]

    victim = [p for p in players if p not in werewolves and p != witch][0]

    actions = {w: victim for w in werewolves}
    actions[witch] = "save"

    print(f"Werewolves attack: {victim}")
    print(f"Witch saves: {victim}")

    game.execute_night_phase(actions)

    if victim in game.state.alive_players:
        print(f"✅ {victim} survived!")
    else:
        print(f"❌ {victim} died!")

    print_separator()


if __name__ == "__main__":
    # Run simple demo
    game = simple_game_demo()

    # Test special rules
    test_special_rules()

    print("\n✅ Demo completed!")
    print("\nTo run a full AI-powered game:")
    print("  python run_game.py")
