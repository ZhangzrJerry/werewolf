// Game log parser - fully featured version matching Flask implementation
export default class GameLogParser {
    constructor() {
        this.events = []
        this.players = {}
        this.game_info = {}
        this.current_round = 0
        this.event_counter = 0
        this.player_death_round = {}
    }

    parseGameLog(logText) {
        // Parse game info
        this.parseGameInfo(logText)

        // Parse rounds using simple approach
        const roundMatches = logText.matchAll(/^ROUND (\d+)$/gm)
        const roundArray = Array.from(roundMatches)

        for (let i = 0; i < roundArray.length; i++) {
            const startIndex = roundArray[i].index
            const endIndex = i + 1 < roundArray.length ? roundArray[i + 1].index : logText.length
            const roundContent = logText.substring(startIndex, endIndex)
            this.parseRound(roundContent)
        }

        // Parse game over
        this.parseGameOver(logText)

        return {
            game_info: this.game_info,
            players: this.players,
            events: this.events
        }
    }

    parseGameInfo(content) {
        // Game type
        const gameTypeMatch = content.match(/Game Type:\s*(\w+)/)
        if (gameTypeMatch) {
            this.game_info.game_type = gameTypeMatch[1]
        }

        // Players - extract all player names - handle line wrapping
        let playerString = ''
        const startIdx = content.indexOf('Players:')
        if (startIdx !== -1) {
            const afterPlayers = content.substring(startIdx + 8) // skip 'Players:'
            // Find the end - either "Werewolf team:" or "Created 12 agents"
            const endIdx = Math.min(
                afterPlayers.indexOf('Werewolf team') !== -1 ? afterPlayers.indexOf('Werewolf team') : afterPlayers.length,
                afterPlayers.indexOf('Created') !== -1 ? afterPlayers.indexOf('Created') : afterPlayers.length
            )
            playerString = afterPlayers.substring(0, endIdx).trim()
        }

        if (playerString) {
            // Split by comma and clean up
            const playerNames = playerString.split(',').map(p => p.trim()).filter(p => p && !p.includes('\n') && p.length > 0 && p.match(/^[A-Za-z]+$/))
            this.game_info.player_names = playerNames
            playerNames.forEach(name => {
                this.players[name] = {
                    name: name,
                    role: 'unknown',
                    status: 'alive',
                    death_round: null,
                    death_reason: null
                }
            })
        }

        // Werewolf team
        const werewolfMatch = content.match(/Werewolf team:\s*([^\n]+)/)
        if (werewolfMatch) {
            this.game_info.werewolf_team = werewolfMatch[1].split(',').map(n => n.trim())
        }

        // Parse all player roles
        const roleStart = content.indexOf('Player Roles:')
        if (roleStart !== -1) {
            const roleEnd = Math.min(
                content.indexOf('WEREWOLF GAME STARTING', roleStart) || content.length,
                content.indexOf('============================================================', roleStart + 50) || content.length
            )
            const roleSection = content.substring(roleStart, roleEnd)
            const roleLines = roleSection.split('\n')

            roleLines.forEach(line => {
                // Match pattern "  PlayerName: role"
                const match = line.match(/\s+([A-Za-z]+):\s+([a-z_]+)/)
                if (match) {
                    const playerName = match[1]
                    const role = match[2]
                    if (this.players[playerName]) {
                        this.players[playerName].role = role
                    }
                }
            })
        }
    }

    parseRound(roundContent) {
        // Extract round number
        const roundMatch = roundContent.match(/ROUND (\d+)/)
        if (roundMatch) {
            this.current_round = parseInt(roundMatch[1])
        }

        // Night phase
        if (roundContent.includes('[NIGHT PHASE]')) {
            this.parseNightPhase(roundContent)
        }

        // Morning announcement
        if (roundContent.includes('[MORNING] Announcement:')) {
            this.parseMorning(roundContent)
        }

        // Day phase
        if (roundContent.includes('[DAY PHASE]')) {
            this.parseDayPhase(roundContent)
        }

        // Voting
        if (roundContent.includes('[VOTING] Voting Phase')) {
            this.parseVoting(roundContent)
        }

        // Elimination
        if (roundContent.includes('[ELIMINATED]')) {
            this.parseElimination(roundContent)
        }

        // Hunter skill
        if (roundContent.includes('[HUNTER SKILL]')) {
            this.parseHunterSkill(roundContent)
        }
    }

    parseNightPhase(content) {
        this.events.push({
            round_num: this.current_round,
            phase: 'night',
            event_type: 'phase_start',
            data: { phase: 'night' },
            timestamp: this.event_counter++
        })

        // Guardian protecting
        if (content.includes('[GUARDIAN]')) {
            const guardianMatch = content.match(/\[GUARDIAN\].*?\n\s*(\w+) protects:\s*(\w+)/)
            if (guardianMatch) {
                this.events.push({
                    round_num: this.current_round,
                    phase: 'night',
                    event_type: 'guardian_action',
                    data: {
                        action: 'protecting',
                        guardian: guardianMatch[1],
                        protected: guardianMatch[2]
                    },
                    timestamp: this.event_counter++
                })
            }
        }

        // Werewolves choosing target
        const werewolfSection = content.match(/\[WEREWOLVES\].*?Choosing target[\s\S]*?\n((?:\s+\w+ targets:[\s\S]*?\n?)+?)(?:\n\[|$)/)
        if (werewolfSection) {
            const targets = {}
            const lines = werewolfSection[1].split('\n')
            lines.forEach(line => {
                const match = line.match(/\s+(\w+)\s+targets:\s*(\w+)/)
                if (match) {
                    targets[match[1]] = match[2]
                }
            })
            if (Object.keys(targets).length > 0) {
                this.events.push({
                    round_num: this.current_round,
                    phase: 'night',
                    event_type: 'werewolf_target',
                    data: { targets: targets },
                    timestamp: this.event_counter++
                })
            }
        }

        // Seer checking
        const seerMatch = content.match(/\[SEER\].*?Checking[\s\S]*?\n\s+(\w+)\s+checks:\s*(\w+)/)
        if (seerMatch) {
            this.events.push({
                round_num: this.current_round,
                phase: 'night',
                event_type: 'seer_check',
                data: { seer: seerMatch[1], target: seerMatch[2] },
                timestamp: this.event_counter++
            })
        }

        // Seer learned
        const seerLearnedMatch = content.match(/\[SEER\].*?Learning[\s\S]*?\n\s+(\w+)\s+learned:\s*(\w+)\s+is\s+(\w+)/)
        if (seerLearnedMatch) {
            this.events.push({
                round_num: this.current_round,
                phase: 'night',
                event_type: 'seer_result',
                data: {
                    seer: seerLearnedMatch[1],
                    target: seerLearnedMatch[2],
                    result: seerLearnedMatch[3]
                },
                timestamp: this.event_counter++
            })
        }

        // Witch save
        const witchSaveMatch = content.match(/\[WITCH\][\s\S]*?(\w+)\s+does not save\s+(\w+)/)
        if (witchSaveMatch) {
            this.events.push({
                round_num: this.current_round,
                phase: 'night',
                event_type: 'witch_save',
                data: {
                    witch: witchSaveMatch[1],
                    target: witchSaveMatch[2],
                    saved: false
                },
                timestamp: this.event_counter++
            })
        }

        const witchSavedMatch = content.match(/\[WITCH\][\s\S]*?(\w+)\s+saves\s+(\w+)/)
        if (witchSavedMatch) {
            this.events.push({
                round_num: this.current_round,
                phase: 'night',
                event_type: 'witch_save',
                data: {
                    witch: witchSavedMatch[1],
                    target: witchSavedMatch[2],
                    saved: true
                },
                timestamp: this.event_counter++
            })
        }

        // Witch poison
        const witchPoisonMatch = content.match(/\[WITCH\][\s\S]*?(\w+)\s+does not use poison/)
        if (witchPoisonMatch) {
            this.events.push({
                round_num: this.current_round,
                phase: 'night',
                event_type: 'witch_poison',
                data: { witch: witchPoisonMatch[1], used: false },
                timestamp: this.event_counter++
            })
        }

        const witchPoisonedMatch = content.match(/\[WITCH\][\s\S]*?(\w+)\s+uses poison on\s+(\w+)/)
        if (witchPoisonedMatch) {
            this.events.push({
                round_num: this.current_round,
                phase: 'night',
                event_type: 'witch_poison',
                data: { witch: witchPoisonedMatch[1], target: witchPoisonedMatch[2], used: true },
                timestamp: this.event_counter++
            })
        }
    }

    parseMorning(content) {
        this.events.push({
            round_num: this.current_round,
            phase: 'morning',
            event_type: 'phase_start',
            data: { phase: 'morning' },
            timestamp: this.event_counter++
        })

        // Death announcement - look for [DEAD] pattern
        const deadMatch = content.match(/\[DEAD\]\s+(\w+)\s+died/)
        if (deadMatch) {
            const deadPlayer = deadMatch[1]
            this.events.push({
                round_num: this.current_round,
                phase: 'morning',
                event_type: 'death_announcement',
                data: { player: deadPlayer },
                timestamp: this.event_counter++
            })
            if (this.players[deadPlayer]) {
                this.players[deadPlayer].status = 'dead'
                this.players[deadPlayer].death_round = this.current_round
            }
            if (!this.player_death_round[deadPlayer]) {
                this.player_death_round[deadPlayer] = this.current_round
            }
        }

        // Check for safe night
        const safeMatch = content.match(/\[SAFE\]\s+Everyone survived/)
        if (safeMatch) {
            this.events.push({
                round_num: this.current_round,
                phase: 'morning',
                event_type: 'safe_night',
                data: { message: 'Everyone survived the night!' },
                timestamp: this.event_counter++
            })
        }
    }

    parseDayPhase(content) {
        this.events.push({
            round_num: this.current_round,
            phase: 'day',
            event_type: 'phase_start',
            data: { phase: 'day' },
            timestamp: this.event_counter++
        })

        // Player discussions - look for content between [DAY PHASE] and [VOTING]
        const discussionSection = content.match(/\[DAY PHASE\]([\s\S]*?)(?:\[VOTING\]|$)/)
        if (discussionSection) {
            const text = discussionSection[1]
            const lines = text.split('\n')
            lines.forEach(line => {
                const trimmedLine = line.trim()
                // Match pattern like "Bob: Some discussion text"
                // This matches lines that start with a word followed by colon
                const match = trimmedLine.match(/^([A-Z][a-z]+):\s+(.+)$/)
                if (match && trimmedLine.length > 5) {
                    const speaker = match[1]
                    const statement = match[2].trim()
                    // Skip system messages and headers
                    if (speaker !== 'Day' && speaker !== 'Alive' && speaker !== 'Players' &&
                        speaker !== 'Discussion' && speaker !== 'Role' &&
                        !trimmedLine.startsWith('---') &&
                        statement.length > 3) {
                        this.events.push({
                            round_num: this.current_round,
                            phase: 'day',
                            event_type: 'discussion',
                            data: {
                                speaker: speaker,
                                statement: statement
                            },
                            timestamp: this.event_counter++
                        })
                    }
                }
            })
        }
    }

    parseVoting(content) {
        this.events.push({
            round_num: this.current_round,
            phase: 'voting',
            event_type: 'phase_start',
            data: { phase: 'voting' },
            timestamp: this.event_counter++
        })

        // Vote counting - match pattern like "  Bob votes for: Eve"
        const voteSection = content.match(/\[VOTING\]([\s\S]*?)(?:\[ELIMINATED\]|$)/)
        if (voteSection) {
            const lines = voteSection[1].split('\n')
            lines.forEach(line => {
                const match = line.match(/\s+(\w+)\s+votes\s+for:\s*(\w+)/)
                if (match) {
                    this.events.push({
                        round_num: this.current_round,
                        phase: 'voting',
                        event_type: 'vote',
                        data: {
                            voter: match[1],
                            target: match[2]
                        },
                        timestamp: this.event_counter++
                    })
                }
            })
        }
    }

    parseElimination(content) {
        // Match [ELIMINATED] section - try different formats
        const eliminationMatch = content.match(/\[ELIMINATED\]\s+(\w+)\s+was eliminated/)
        if (eliminationMatch) {
            const eliminated = eliminationMatch[1]

            // Try to capture the role on the next line
            const roleMatch = content.match(new RegExp(`\\[ELIMINATED\\]\\s+${eliminated}.*?\\n\\s+Role:\\s*(\\w+)`))
            const role = roleMatch ? roleMatch[1] : null

            this.events.push({
                round_num: this.current_round,
                phase: 'day',
                event_type: 'elimination',
                data: {
                    player: eliminated,
                    role: role
                },
                timestamp: this.event_counter++
            })

            // Record death for this player
            if (!this.player_death_round[eliminated]) {
                this.player_death_round[eliminated] = this.current_round
            }

            if (this.players[eliminated]) {
                this.players[eliminated].status = 'dead'
                this.players[eliminated].death_round = this.current_round
            }
        }

        this.events.push({
            round_num: this.current_round,
            phase: 'day',
            event_type: 'phase_end',
            data: { phase: 'day' },
            timestamp: this.event_counter++
        })
    }

    parseHunterSkill(content) {
        // Match [HUNTER SKILL] section
        const hunterMatch = content.match(/\[HUNTER SKILL\]\s+(\w+)\s+.*?(?:shoots|targets)\s+(\w+)/)
        if (hunterMatch) {
            const hunter = hunterMatch[1]
            const target = hunterMatch[2]
            this.events.push({
                round_num: this.current_round,
                phase: 'day',
                event_type: 'hunter_skill',
                data: {
                    hunter: hunter,
                    target: target
                },
                timestamp: this.event_counter++
            })

            // Record target death
            if (!this.player_death_round[target]) {
                this.player_death_round[target] = this.current_round
            }
            if (this.players[target]) {
                this.players[target].status = 'dead'
                this.players[target].death_round = this.current_round
            }
        }
    }

    parseGameOver(content) {
        // Look for game end messages - try different patterns
        if (content.includes('[WINNER] WEREWOLVES') || content.includes('Werewolves win') || content.includes('werewolves win')) {
            this.game_info.winner = 'werewolves'
            this.events.push({
                round_num: this.current_round,
                phase: 'end',
                event_type: 'game_end',
                data: {
                    winner: 'werewolves',
                    message: 'Werewolves win!'
                },
                timestamp: this.event_counter++
            })
        } else if (content.includes('[WINNER] VILLAGERS') || content.includes('Villagers win') || content.includes('villagers win')) {
            this.game_info.winner = 'villagers'
            this.events.push({
                round_num: this.current_round,
                phase: 'end',
                event_type: 'game_end',
                data: {
                    winner: 'villagers',
                    message: 'Villagers win!'
                },
                timestamp: this.event_counter++
            })
        }

        // Parse rounds played
        const roundsMatch = content.match(/Rounds played:\s*(\d+)/)
        if (roundsMatch) {
            this.game_info.rounds_played = parseInt(roundsMatch[1])
        }
    }

    getPlayerStateAtEvent(playerName, eventIndex) {
        // Get player state at specific event index
        if (!this.players[playerName]) {
            return { status: 'alive' }
        }

        // Check if player died before or at this event
        for (let i = 0; i <= eventIndex && i < this.events.length; i++) {
            const event = this.events[i]
            if ((event.event_type === 'death_announcement' || event.event_type === 'elimination')
                && event.data.player === playerName) {
                return {
                    status: 'dead',
                    role: this.players[playerName].role
                }
            }
        }

        // Player is alive
        return {
            status: 'alive',
            role: this.players[playerName].role
        }
    }
}
