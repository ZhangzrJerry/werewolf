"""
State manager for game visualization
"""

from typing import Dict, List, Any
from parser import GameEvent, Player


class GameStateManager:
    def __init__(self, parsed_data: Dict[str, Any]):
        self.game_info = parsed_data["game_info"]
        self.players = parsed_data["players"]
        self.events = parsed_data["events"]

        self.current_event_index = 0
        self.current_round = 0
        self.current_phase = "start"

        # Track current state for visualization
        self.current_player_states = {}
        self._initialize_player_states()

    def _initialize_player_states(self):
        """Initialize all players as alive with their actual roles"""
        for name, player in self.players.items():
            self.current_player_states[name] = {
                "name": name,
                "status": "alive",
                "role": player.role,  # Use actual role from log instead of "unknown"
                "revealed": True,     # Show actual roles from the beginning
            }

    def get_current_state(self) -> Dict[str, Any]:
        """Get the current game state"""
        if self.current_event_index >= len(self.events):
            event = None
        else:
            event = self.events[self.current_event_index]

        return {
            "event_index": self.current_event_index,
            "total_events": len(self.events),
            "current_event": event,
            "player_states": self.current_player_states,
            "game_info": self.game_info,
            "is_finished": self.current_event_index >= len(self.events),
        }

    def next_event(self) -> Dict[str, Any]:
        """Move to the next event and update state"""
        if self.current_event_index < len(self.events):
            event = self.events[self.current_event_index]
            self._apply_event(event)
            self.current_event_index += 1
            self.current_round = event.round_num
            self.current_phase = event.phase

        return self.get_current_state()

    def prev_event(self) -> Dict[str, Any]:
        """Move to the previous event"""
        if self.current_event_index > 0:
            self.current_event_index -= 1
            self._rebuild_state_up_to_current()

            if self.current_event_index > 0:
                event = self.events[self.current_event_index - 1]
                self.current_round = event.round_num
                self.current_phase = event.phase

        return self.get_current_state()

    def jump_to_event(self, event_index: int) -> Dict[str, Any]:
        """Jump to a specific event"""
        if 0 <= event_index <= len(self.events):
            self.current_event_index = event_index
            self._rebuild_state_up_to_current()

            if self.current_event_index > 0 and self.current_event_index <= len(
                self.events
            ):
                event = self.events[self.current_event_index - 1]
                self.current_round = event.round_num
                self.current_phase = event.phase

        return self.get_current_state()

    def jump_to_round(self, round_num: int) -> Dict[str, Any]:
        """Jump to the start of a specific round"""
        for i, event in enumerate(self.events):
            if event.round_num == round_num:
                return self.jump_to_event(i)

        return self.get_current_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to the beginning"""
        self.current_event_index = 0
        self.current_round = 0
        self.current_phase = "start"
        self._initialize_player_states()
        return self.get_current_state()

    def _apply_event(self, event: GameEvent):
        """Apply an event to update the current state"""
        if event.event_type == "death_announcement":
            player_name = event.data["player"]
            if player_name in self.current_player_states:
                self.current_player_states[player_name]["status"] = "dead"

        elif event.event_type == "elimination":
            player_name = event.data["player"]
            role = event.data["role"]
            if player_name in self.current_player_states:
                self.current_player_states[player_name]["status"] = "dead"
                self.current_player_states[player_name]["role"] = role
                self.current_player_states[player_name]["revealed"] = True

    def _rebuild_state_up_to_current(self):
        """Rebuild the state by replaying all events up to current index"""
        self._initialize_player_states()

        for i in range(self.current_event_index):
            self._apply_event(self.events[i])

    def get_alive_players(self) -> List[str]:
        """Get list of currently alive players"""
        return [
            name
            for name, state in self.current_player_states.items()
            if state["status"] == "alive"
        ]

    def get_dead_players(self) -> List[str]:
        """Get list of currently dead players"""
        return [
            name
            for name, state in self.current_player_states.items()
            if state["status"] == "dead"
        ]
