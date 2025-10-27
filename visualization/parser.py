"""
Game log parser for Werewolf game visualization
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class Player:
    name: str
    role: str = "unknown"
    status: str = "alive"  # alive, dead
    death_round: int = None
    death_reason: str = None


@dataclass
class GameEvent:
    round_num: int
    phase: str  # night, morning, day, voting, elimination
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: int = 0  # Sequential timestamp for animation


class GameLogParser:
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.events: List[GameEvent] = []
        self.players: Dict[str, Player] = {}
        self.game_info: Dict[str, Any] = {}
        self.current_round = 0
        self.event_counter = 0

    def parse(self) -> Dict[str, Any]:
        """Parse the game log file and extract all events"""
        with open(self.log_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse game info
        self._parse_game_info(content)

        # Parse rounds
        rounds = re.split(r"={60}\nROUND \d+\n={60}", content)

        for i, round_content in enumerate(rounds[1:], start=1):
            self.current_round = i
            self._parse_round(round_content)

        # Parse game over
        self._parse_game_over(content)

        return {
            "game_info": self.game_info,
            "players": self.players,
            "events": self.events,
        }

    def _parse_game_info(self, content: str):
        """Parse basic game information"""
        # Game type
        game_type_match = re.search(r"Game Type: (\w+)", content)
        if game_type_match:
            self.game_info["game_type"] = game_type_match.group(1)

        # Players
        players_match = re.search(r"Players: ([^\n]+)", content)
        if players_match:
            player_names = [name.strip() for name in players_match.group(1).split(",")]
            self.game_info["player_names"] = player_names
            for name in player_names:
                self.players[name] = Player(name=name)

        # Werewolf team
        werewolf_match = re.search(r"Werewolf team: ([^\n]+)", content)
        if werewolf_match:
            werewolf_names = [
                name.strip() for name in werewolf_match.group(1).split(",")
            ]
            self.game_info["werewolf_team"] = werewolf_names

    def _parse_round(self, round_content: str):
        """Parse a single round"""
        # Night phase
        if "[NIGHT PHASE]" in round_content:
            self._parse_night_phase(round_content)

        # Morning announcement
        if "[MORNING] Announcement:" in round_content:
            self._parse_morning(round_content)

        # Day phase
        if "[DAY PHASE]" in round_content:
            self._parse_day_phase(round_content)

        # Voting
        if "[VOTING] Voting Phase" in round_content:
            self._parse_voting(round_content)

        # Elimination
        if "[ELIMINATED]" in round_content:
            self._parse_elimination(round_content)

    def _parse_night_phase(self, content: str):
        """Parse night phase events"""
        self.events.append(
            GameEvent(
                round_num=self.current_round,
                phase="night",
                event_type="phase_start",
                data={"phase": "night"},
                timestamp=self.event_counter,
            )
        )
        self.event_counter += 1

        # Guardian protecting
        if "[GUARDIAN] Protecting..." in content:
            # Try to find who the guardian protected
            guardian_protect_match = re.search(r"  (\w+) protects: (\w+)", content)
            if guardian_protect_match:
                guardian, protected = guardian_protect_match.groups()
                self.events.append(
                    GameEvent(
                        round_num=self.current_round,
                        phase="night",
                        event_type="guardian_action",
                        data={
                            "action": "protecting",
                            "guardian": guardian,
                            "protected": protected,
                        },
                        timestamp=self.event_counter,
                    )
                )
            else:
                # No guardian in this game or guardian didn't protect anyone
                self.events.append(
                    GameEvent(
                        round_num=self.current_round,
                        phase="night",
                        event_type="guardian_action",
                        data={"action": "no_protection"},
                        timestamp=self.event_counter,
                    )
                )
            self.event_counter += 1

        # Werewolves choosing target
        werewolf_section = re.search(
            r"\[WEREWOLVES\] Choosing target\.\.\.\n((?:  \w+ targets: \w+\n)+)",
            content,
        )
        if werewolf_section:
            targets = {}
            # Don't use strip() - it removes leading spaces from first line
            for line in werewolf_section.group(1).split("\n"):
                if line:  # Skip empty lines
                    match = re.match(r"  (\w+) targets: (\w+)", line)
                    if match:
                        werewolf, target = match.groups()
                        targets[werewolf] = target

            self.events.append(
                GameEvent(
                    round_num=self.current_round,
                    phase="night",
                    event_type="werewolf_target",
                    data={"targets": targets},
                    timestamp=self.event_counter,
                )
            )
            self.event_counter += 1

        # Seer checking
        seer_match = re.search(r"  (\w+) checks: (\w+)", content)
        if seer_match:
            seer, target = seer_match.groups()
            self.events.append(
                GameEvent(
                    round_num=self.current_round,
                    phase="night",
                    event_type="seer_check",
                    data={"seer": seer, "target": target},
                    timestamp=self.event_counter,
                )
            )
            self.event_counter += 1

        # Witch decisions
        witch_save_match = re.search(r"  (\w+) does not save (\w+)", content)
        if witch_save_match:
            witch, target = witch_save_match.groups()
            self.events.append(
                GameEvent(
                    round_num=self.current_round,
                    phase="night",
                    event_type="witch_save",
                    data={"witch": witch, "target": target, "saved": False},
                    timestamp=self.event_counter,
                )
            )
            self.event_counter += 1

        witch_poison_match = re.search(r"  (\w+) does not use poison", content)
        if witch_poison_match:
            witch = witch_poison_match.group(1)
            self.events.append(
                GameEvent(
                    round_num=self.current_round,
                    phase="night",
                    event_type="witch_poison",
                    data={"witch": witch, "used": False},
                    timestamp=self.event_counter,
                )
            )
            self.event_counter += 1

        # Seer learned
        seer_learned_match = re.search(r"  (\w+) learned: (\w+) is (\w+)", content)
        if seer_learned_match:
            seer, target, result = seer_learned_match.groups()
            self.events.append(
                GameEvent(
                    round_num=self.current_round,
                    phase="night",
                    event_type="seer_result",
                    data={"seer": seer, "target": target, "result": result},
                    timestamp=self.event_counter,
                )
            )
            self.event_counter += 1

    def _parse_morning(self, content: str):
        """Parse morning announcements"""
        dead_match = re.search(
            r"\[DEAD\] (\w+) died during the night \((\w+)\)", content
        )
        if dead_match:
            player_name, reason = dead_match.groups()

            self.events.append(
                GameEvent(
                    round_num=self.current_round,
                    phase="morning",
                    event_type="death_announcement",
                    data={"player": player_name, "reason": reason},
                    timestamp=self.event_counter,
                )
            )
            self.event_counter += 1

            # Update player status
            if player_name in self.players:
                self.players[player_name].status = "dead"
                self.players[player_name].death_round = self.current_round
                self.players[player_name].death_reason = reason

            # Last words
            last_words_match = re.search(
                rf"\[LAST WORDS\] {player_name}\'s final statement:\n  {player_name}: ([^\n]+)",
                content,
            )
            if last_words_match:
                statement = last_words_match.group(1)
                self.events.append(
                    GameEvent(
                        round_num=self.current_round,
                        phase="morning",
                        event_type="last_words",
                        data={"player": player_name, "statement": statement},
                        timestamp=self.event_counter,
                    )
                )
                self.event_counter += 1

    def _parse_day_phase(self, content: str):
        """Parse day phase discussions"""
        self.events.append(
            GameEvent(
                round_num=self.current_round,
                phase="day",
                event_type="phase_start",
                data={"phase": "day"},
                timestamp=self.event_counter,
            )
        )
        self.event_counter += 1

        # Alive players
        alive_match = re.search(r"Alive players: ([^\n]+)", content)
        if alive_match:
            alive_players = [name.strip() for name in alive_match.group(1).split(",")]
            self.events.append(
                GameEvent(
                    round_num=self.current_round,
                    phase="day",
                    event_type="alive_players",
                    data={"players": alive_players},
                    timestamp=self.event_counter,
                )
            )
            self.event_counter += 1

        # Discussion
        discussion_pattern = r"(\w+): ([^\n]+(?:\n(?!\w+:)[^\n]+)*)"
        discussions = re.findall(discussion_pattern, content)

        for speaker, statement in discussions:
            if speaker in self.players:
                self.events.append(
                    GameEvent(
                        round_num=self.current_round,
                        phase="day",
                        event_type="discussion",
                        data={"speaker": speaker, "statement": statement.strip()},
                        timestamp=self.event_counter,
                    )
                )
                self.event_counter += 1

    def _parse_voting(self, content: str):
        """Parse voting phase"""
        self.events.append(
            GameEvent(
                round_num=self.current_round,
                phase="voting",
                event_type="phase_start",
                data={"phase": "voting"},
                timestamp=self.event_counter,
            )
        )
        self.event_counter += 1

        vote_pattern = r"  (\w+) votes for: (\w+)"
        votes = re.findall(vote_pattern, content)

        vote_data = {}
        for voter, target in votes:
            if target not in vote_data:
                vote_data[target] = []
            vote_data[target].append(voter)

            self.events.append(
                GameEvent(
                    round_num=self.current_round,
                    phase="voting",
                    event_type="vote",
                    data={"voter": voter, "target": target},
                    timestamp=self.event_counter,
                )
            )
            self.event_counter += 1

        # Vote summary
        self.events.append(
            GameEvent(
                round_num=self.current_round,
                phase="voting",
                event_type="vote_summary",
                data={"votes": vote_data},
                timestamp=self.event_counter,
            )
        )
        self.event_counter += 1

    def _parse_elimination(self, content: str):
        """Parse elimination"""
        elim_match = re.search(
            r"\[ELIMINATED\] (\w+) was eliminated by vote!\n   Role: (\w+)", content
        )
        if elim_match:
            player_name, role = elim_match.groups()

            self.events.append(
                GameEvent(
                    round_num=self.current_round,
                    phase="voting",
                    event_type="elimination",
                    data={"player": player_name, "role": role},
                    timestamp=self.event_counter,
                )
            )
            self.event_counter += 1

            # Update player info
            if player_name in self.players:
                self.players[player_name].status = "dead"
                self.players[player_name].role = role
                self.players[player_name].death_round = self.current_round
                self.players[player_name].death_reason = "eliminated"

            # Last words
            last_words_match = re.search(
                rf"\[LAST WORDS\] {player_name}\'s final statement:\n  {player_name}: ([^\n]+)",
                content,
            )
            if last_words_match:
                statement = last_words_match.group(1)
                self.events.append(
                    GameEvent(
                        round_num=self.current_round,
                        phase="voting",
                        event_type="last_words",
                        data={"player": player_name, "statement": statement},
                        timestamp=self.event_counter,
                    )
                )
                self.event_counter += 1

            # Hunter skill activation
            hunter_skill_match = re.search(
                rf"\[HUNTER SKILL\] {player_name} activates hunter ability!\n  {player_name} shoots (\w+)!\n  (\w+) \((\w+)\) is killed!",
                content,
            )
            if hunter_skill_match:
                target = hunter_skill_match.group(1)
                target_confirm = hunter_skill_match.group(2)
                target_role = hunter_skill_match.group(3)

                self.events.append(
                    GameEvent(
                        round_num=self.current_round,
                        phase="voting",
                        event_type="hunter_skill",
                        data={
                            "hunter": player_name,
                            "target": target,
                            "target_role": target_role,
                        },
                        timestamp=self.event_counter,
                    )
                )
                self.event_counter += 1

                # Update target player status
                if target in self.players:
                    self.players[target].status = "dead"
                    self.players[target].role = target_role
                    self.players[target].death_round = self.current_round
                    self.players[target].death_reason = "hunter_shot"

    def _parse_game_over(self, content: str):
        """Parse game over information"""
        game_over_section = re.search(
            r"={60}\nGAME OVER\n={60}\n(.*?)(?:\[LEARNING\]|$)", content, re.DOTALL
        )

        if game_over_section:
            game_over_content = game_over_section.group(1)

            # Winner
            winner_match = re.search(r"\[WINNER\] (\w+)", game_over_content)
            if winner_match:
                self.game_info["winner"] = winner_match.group(1)

            # Rounds played
            rounds_match = re.search(r"Rounds played: (\d+)", game_over_content)
            if rounds_match:
                self.game_info["rounds_played"] = int(rounds_match.group(1))

            # Final roles
            role_pattern = r"\[(?:DEAD|ALIVE)\] (\w+): (\w+)"
            roles = re.findall(role_pattern, game_over_content)

            for player_name, role in roles:
                if player_name in self.players:
                    self.players[player_name].role = role

            self.game_info["final_roles"] = {name: role for name, role in roles}
