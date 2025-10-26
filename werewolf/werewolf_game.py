import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any


class Role(Enum):
    WEREWOLF = "werewolf"
    VILLAGER = "villager"
    SEER = "seer"
    WITCH = "witch"
    HUNTER = "hunter"
    GUARDIAN = "guardian"

    def is_werewolf(self) -> bool:
        """Check if this role is on the werewolf team"""
        return self == Role.WEREWOLF

    def get_team(self) -> str:
        """Get team name: 'good' or 'werewolf'"""
        return "werewolf" if self.is_werewolf() else "good"


class GamePhase(Enum):
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"


@dataclass
class GameState:
    players: List[str]
    roles: Dict[str, Role]
    alive_players: List[str]
    phase: GamePhase
    day_count: int
    history: List[Dict[str, Any]]
    game_log: List[str]
    witch_poison_used: bool = False
    witch_antidote_used: bool = False
    guardian_last_guarded: Dict[str, str] | None = None
    death_records: Dict[str, str] = None  # Track how each player died

    def __post_init__(self):
        if self.death_records is None:
            self.death_records = {}


class WerewolfGame:
    """A minimal, deterministic implementation of core Werewolf game rules.

    Responsibilities:
    - assign roles according to a simple preset per `game_type`
    - run night actions (werewolves, seer, witch)
    - run day actions (voting)
    - determine game end conditions
    """

    def __init__(self, player_names: List[str], game_type: str = "six"):
        if len(player_names) < 4:
            raise ValueError("Need at least 4 players to play")

        self.player_names = list(player_names)
        self.game_type = game_type
        self.state = GameState(
            players=self.player_names.copy(),
            roles={},
            alive_players=self.player_names.copy(),
            phase=GamePhase.NIGHT,
            day_count=0,
            history=[],
            game_log=[],
            witch_poison_used=False,
            witch_antidote_used=False,
        )

        self._assign_roles()

    def _assign_roles(self):
        """Assign roles based on `game_type` presets."""
        if self.game_type == "six":
            roles = [
                Role.WEREWOLF,
                Role.WEREWOLF,
                Role.VILLAGER,
                Role.VILLAGER,
                Role.SEER,
                Role.WITCH,
            ]
        elif self.game_type == "nine":
            roles = [
                Role.WEREWOLF,
                Role.WEREWOLF,
                Role.WEREWOLF,
                Role.VILLAGER,
                Role.VILLAGER,
                Role.VILLAGER,
                Role.SEER,
                Role.WITCH,
                Role.HUNTER,
            ]
        else:  # default to twelve-like
            roles = [
                Role.WEREWOLF,
                Role.WEREWOLF,
                Role.WEREWOLF,
                Role.WEREWOLF,
                Role.VILLAGER,
                Role.VILLAGER,
                Role.VILLAGER,
                Role.VILLAGER,
                Role.SEER,
                Role.WITCH,
                Role.HUNTER,
                Role.GUARDIAN,
            ]

        random.shuffle(roles)
        # If there are more players than roles in the selected preset, fill extras with villagers
        if len(self.player_names) > len(roles):
            roles.extend([Role.VILLAGER] * (len(self.player_names) - len(roles)))

        self.state.roles = {p: r for p, r in zip(self.player_names, roles)}
        self.state.game_log.append(f"Roles assigned: {[r.value for r in roles]}")

    def _get_players_with_role(self, role: Role) -> List[str]:
        return [p for p in self.state.alive_players if self.state.roles.get(p) == role]

    def _process_werewolf_action(self, agent_actions: Dict[str, str]) -> str:
        """Werewolves choose a target by majority among their picks. Returns target or empty string."""
        werewolves = [
            p
            for p in self.state.alive_players
            if self.state.roles.get(p) == Role.WEREWOLF
        ]
        votes: Dict[str, int] = {}
        for w in werewolves:
            target = agent_actions.get(w)
            if target and target in self.state.alive_players and target != w:
                votes[target] = votes.get(target, 0) + 1

        if not votes:
            return ""

        target = max(votes.items(), key=lambda x: x[1])[0]
        self.state.game_log.append(f"Werewolves attacked {target}")
        return target

    def _process_seer_action(self, agent_actions: Dict[str, str]) -> Dict[str, Role]:
        results: Dict[str, Role] = {}
        seers = [
            p for p in self.state.alive_players if self.state.roles.get(p) == Role.SEER
        ]
        for s in seers:
            target = agent_actions.get(s)
            if target and target in self.state.alive_players:
                results[s] = self.state.roles.get(target)
                self.state.game_log.append(
                    f"Seer {s} checked {target}: {self.state.roles.get(target).value}"
                )
        return results

    def _process_witch_action(
        self, agent_actions: Dict[str, str], night_victim: str | None
    ) -> Dict[str, Any]:
        """Witch can save the night victim (antidote) or poison someone (once each)."""
        res: Dict[str, Any] = {}
        witches = [
            p for p in self.state.alive_players if self.state.roles.get(p) == Role.WITCH
        ]
        for w in witches:
            action = agent_actions.get(w)
            if not action:
                continue
            # expected actions: 'save', 'poison:<name>', 'pass'
            if action == "save" and not self.state.witch_antidote_used and night_victim:
                res["saved"] = night_victim
                self.state.witch_antidote_used = True
                self.state.game_log.append(
                    f"Witch {w} used antidote to save {night_victim}"
                )
            elif action.startswith("poison:") and not self.state.witch_poison_used:
                _, _, target = action.partition(":")
                if target in self.state.alive_players:
                    res["poisoned"] = target
                    self.state.witch_poison_used = True
                    self.state.game_log.append(f"Witch {w} poisoned {target}")
            else:
                self.state.game_log.append(
                    f"Witch {w} did nothing or action invalid: {action}"
                )
        return res

    def _process_guardian_action(self, agent_actions: Dict[str, str]) -> Dict[str, Any]:
        """Guardian can protect one player per night. Cannot protect the same player two nights in a row."""
        res: Dict[str, Any] = {}
        guardians = [
            p
            for p in self.state.alive_players
            if self.state.roles.get(p) == Role.GUARDIAN
        ]
        if self.state.guardian_last_guarded is None:
            self.state.guardian_last_guarded = {}

        for g in guardians:
            target = agent_actions.get(g)
            if not target or target not in self.state.alive_players:
                self.state.game_log.append(
                    f"Guardian {g} did not choose a valid target"
                )
                continue

            last = self.state.guardian_last_guarded.get(g)
            if last and last == target:
                # disallow guarding same player consecutively
                self.state.game_log.append(
                    f"Guardian {g} attempted to guard {target} again and failed"
                )
                continue

            # valid guard
            res["guarded"] = target
            self.state.guardian_last_guarded[g] = target
            self.state.game_log.append(f"Guardian {g} guarded {target} this night")

        return res

    def _collect_votes(self, agent_actions: Dict[str, str]) -> Dict[str, str]:
        votes: Dict[str, str] = {}
        for p, action in agent_actions.items():
            if (
                p in self.state.alive_players
                and action in self.state.alive_players
                and action != p
            ):
                votes[p] = action
        return votes

    def _count_votes(self, votes: Dict[str, str]) -> str:
        if not votes:
            return ""
        tally: Dict[str, int] = {}
        for voter, target in votes.items():
            tally[target] = tally.get(target, 0) + 1

        max_votes = max(tally.values())
        candidates = [t for t, c in tally.items() if c == max_votes]
        if len(candidates) == 1:
            return candidates[0]
        return ""  # tie -> no elimination

    def execute_night_phase(self, agent_actions: Dict[str, str]) -> Dict[str, Any]:
        """Run night: werewolves attack, seer checks, witch may act."""
        night_result: Dict[str, Any] = {}

        # Werewolf attack
        victim = self._process_werewolf_action(agent_actions)
        night_result["werewolf_target"] = victim
        for w in self._get_players_with_role(Role.WEREWOLF):
            w.record_kill_result(victim)

        # Seer
        seer_checks = self._process_seer_action(agent_actions)
        night_result["seer_checks"] = seer_checks

        # Guardian actions
        guardian_result = self._process_guardian_action(agent_actions)
        night_result["guardian"] = guardian_result

        # Witch actions
        witch_result = self._process_witch_action(
            agent_actions, victim if victim else None
        )
        night_result.update(witch_result)

        # Determine final outcome for the night victim.
        # Rule change: if guardian guarded the victim AND witch used antidote on the same victim, the victim dies.
        final_victim = victim

        # Handle poison first (poison always kills)
        if "poisoned" in witch_result:
            poisoned = witch_result["poisoned"]
            if poisoned in self.state.alive_players:
                self.state.alive_players.remove(poisoned)
                self.state.death_records[poisoned] = "witch_poison"
                self.state.game_log.append(f"{poisoned} died by witch poison")
                night_result["poisoned_player"] = poisoned

        # If there was an incoming werewolf attack, decide based on guardian + witch
        if victim:
            guarded = (
                "guarded" in guardian_result
                and guardian_result.get("guarded") == victim
            )
            saved = "saved" in witch_result and witch_result.get("saved") == victim

            if guarded and saved:
                # New rule: both guardian and witch applied -> victim dies
                final_victim = victim
                self.state.game_log.append(
                    f"{victim} was guarded and witch saved; per rule the victim dies"
                )
            elif guarded:
                final_victim = None
                self.state.game_log.append(f"{victim} was protected by guardian")
            elif saved:
                final_victim = None
                self.state.game_log.append(f"{victim} was saved by witch")

        # Apply final victim removal (if any)
        if final_victim and final_victim in self.state.alive_players:
            self.state.alive_players.remove(final_victim)
            self.state.death_records[final_victim] = "werewolf_kill"
            self.state.game_log.append(f"{final_victim} was killed at night")
            night_result["night_death"] = final_victim

        self.state.phase = GamePhase.DAY
        return night_result

    def execute_day_phase(self, agent_actions: Dict[str, str]) -> Dict[str, Any]:
        """Run day: collect votes and eliminate majority if any."""
        votes = self._collect_votes(agent_actions)
        eliminated = self._count_votes(votes)
        day_result: Dict[str, Any] = {"votes": votes, "eliminated": eliminated}

        if eliminated:
            if eliminated in self.state.alive_players:
                self.state.alive_players.remove(eliminated)
                self.state.death_records[eliminated] = "voted_out"
                self.state.game_log.append(f"{eliminated} was voted out during the day")

        self.state.day_count += 1
        self.state.phase = GamePhase.NIGHT
        return day_result

    def check_game_end(self) -> tuple[bool, str]:
        """Return (ended: bool, winner: 'werewolves'|'villagers'|'').

        Victory conditions:
        - 6-player game: Werewolves win if all civilians and gods are eliminated
        - 9 and 12-player games: Werewolves win if all civilians OR all gods are eliminated
        - Villagers win if all werewolves are eliminated
        """
        werewolves_alive = [
            p
            for p in self.state.alive_players
            if self.state.roles.get(p) == Role.WEREWOLF
        ]

        # God roles: Seer, Witch, Guardian, Hunter
        gods_alive = [
            p
            for p in self.state.alive_players
            if self.state.roles.get(p)
            in [Role.SEER, Role.WITCH, Role.GUARDIAN, Role.HUNTER]
        ]

        # Regular villagers
        civilians_alive = [
            p
            for p in self.state.alive_players
            if self.state.roles.get(p) == Role.VILLAGER
        ]

        # Villagers win if all werewolves are eliminated
        if len(werewolves_alive) == 0:
            return True, "villagers"

        # Werewolf victory conditions based on game type
        total_players = len(self.state.players)

        if total_players == 6:
            # 6-player: Must eliminate ALL civilians AND gods
            if len(civilians_alive) == 0 and len(gods_alive) == 0:
                return True, "werewolves"
        else:
            # 9 and 12-player: Eliminate all civilians OR all gods
            if len(civilians_alive) == 0 or len(gods_alive) == 0:
                return True, "werewolves"

        # Traditional fallback: werewolves >= good players
        if len(werewolves_alive) >= len(civilians_alive) + len(gods_alive):
            return True, "werewolves"

        return False, ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "players": self.state.players,
            "roles": {p: r.value for p, r in self.state.roles.items()},
            "alive": self.state.alive_players,
            "phase": self.state.phase.value,
            "day_count": self.state.day_count,
            "game_log": self.state.game_log,
        }
