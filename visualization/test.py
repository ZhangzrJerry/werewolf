"""
Quick test script to verify the visualization system
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parser import GameLogParser
from state_manager import GameStateManager


def test_parser():
    """Test the parser with an actual log file"""
    print("=" * 60)
    print("Testing Parser")
    print("=" * 60)

    # Find a log file
    logs_dir = Path(__file__).parent.parent / ".training" / "game_logs"

    if not logs_dir.exists():
        print("❌ Game logs directory not found!")
        return False

    log_files = list(logs_dir.glob("*.txt"))

    if not log_files:
        print("❌ No log files found!")
        return False

    # Use the first log file
    log_file = log_files[0]
    print(f"📄 Testing with: {log_file.name}")

    try:
        parser = GameLogParser(str(log_file))
        parsed_data = parser.parse()

        print(f"✅ Game Type: {parsed_data['game_info'].get('game_type', 'N/A')}")
        print(f"✅ Players: {len(parsed_data['players'])}")
        print(f"✅ Events: {len(parsed_data['events'])}")
        print(f"✅ Winner: {parsed_data['game_info'].get('winner', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ Parser failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_state_manager():
    """Test the state manager"""
    print("\n" + "=" * 60)
    print("Testing State Manager")
    print("=" * 60)

    logs_dir = Path(__file__).parent.parent / ".training" / "game_logs"
    log_files = list(logs_dir.glob("*.txt"))

    if not log_files:
        print("❌ No log files found!")
        return False

    log_file = log_files[0]

    try:
        parser = GameLogParser(str(log_file))
        parsed_data = parser.parse()

        state_manager = GameStateManager(parsed_data)

        print(f"✅ Initial state created")

        # Test navigation
        state = state_manager.next_event()
        print(f"✅ Next event: {state['event_index']}/{state['total_events']}")

        state = state_manager.next_event()
        print(f"✅ Next event: {state['event_index']}/{state['total_events']}")

        state = state_manager.prev_event()
        print(f"✅ Prev event: {state['event_index']}/{state['total_events']}")

        state = state_manager.reset()
        print(f"✅ Reset: {state['event_index']}/{state['total_events']}")

        return True

    except Exception as e:
        print(f"❌ State manager failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("\n" + "🐺" * 30)
    print("狼人杀可视化系统 - 快速测试")
    print("🐺" * 30 + "\n")

    parser_ok = test_parser()
    state_ok = test_state_manager()

    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)

    if parser_ok and state_ok:
        print("✅ 所有测试通过!")
        print("\n🚀 可以运行 'python app.py' 启动应用")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
