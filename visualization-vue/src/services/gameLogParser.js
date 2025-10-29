// Game log parser - migrated from Python parser logic
export default class GameLogParser {
    constructor() {
        this.events = []
        this.players = {}
        this.game_info = {}
        this.player_states = {}
    }

    parseGameLog(logText) {
        const lines = logText.split('\n')
        let currentRound = 1
        let currentPhase = 'start'
        let eventIndex = 0

        this.events = []
        this.players = {}
        this.game_info = {}
        this.player_states = {}

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim()
            if (!line) continue

            // Parse different types of events
            const event = this.parseLine(line, currentRound, currentPhase, eventIndex)
            if (event) {
                this.events.push(event)
                eventIndex++

                // Update game state based on event
                this.updateGameState(event)

                // Update phase/round tracking
                if (event.event_type === 'phase_start') {
                    currentPhase = event.data.phase
                    if (currentPhase === 'night' && eventIndex > 1) {
                        currentRound++
                    }
                }
            }
        }

        // Set final game info
        this.game_info.rounds_played = currentRound
        this.game_info.game_type = '狼人杀'

        // Determine winner from final events
        const lastEvents = this.events.slice(-5)
        for (const event of lastEvents) {
            if (event.data && typeof event.data === 'string') {
                if (event.data.includes('狼人获胜') || event.data.includes('werewolves win')) {
                    this.game_info.winner = '狼人'
                    break
                } else if (event.data.includes('村民获胜') || event.data.includes('villagers win')) {
                    this.game_info.winner = '村民'
                    break
                }
            }
        }

        return {
            events: this.events,
            players: this.players,
            game_info: this.game_info
        }
    }

    parseLine(line, round, phase, eventIndex) {
        // Skip certain lines
        if (line.startsWith('=') || line.startsWith('[INFO]') || line.startsWith('[DEBUG]')) {
            return null
        }

        // Phase transitions
        if (line.includes('夜晚阶段') || line.includes('Night phase')) {
            return {
                event_type: 'phase_start',
                round_num: round,
                phase: 'night',
                data: { phase: 'night' },
                index: eventIndex
            }
        }

        if (line.includes('白天阶段') || line.includes('Day phase')) {
            return {
                event_type: 'phase_start',
                round_num: round,
                phase: 'day',
                data: { phase: 'day' },
                index: eventIndex
            }
        }

        if (line.includes('投票阶段') || line.includes('Voting phase')) {
            return {
                event_type: 'phase_start',
                round_num: round,
                phase: 'voting',
                data: { phase: 'voting' },
                index: eventIndex
            }
        }

        // Player actions
        if (line.includes('说:') || line.includes(' says:')) {
            const match = line.match(/^(.+?)\s*说:\s*(.+)$/) || line.match(/^(.+?)\s*says:\s*(.+)$/)
            if (match) {
                const speaker = match[1].trim()
                const statement = match[2].trim()

                // Register player if not seen
                if (!this.players[speaker]) {
                    this.players[speaker] = {
                        name: speaker,
                        role: 'unknown',
                        status: 'alive'
                    }
                }

                return {
                    event_type: 'discussion',
                    round_num: round,
                    phase: phase,
                    data: { speaker, statement },
                    index: eventIndex
                }
            }
        }

        // Deaths
        if (line.includes('死了') || line.includes('died') || line.includes('was killed')) {
            const playerMatch = line.match(/(\w+)\s*(死了|died|was killed)/)
            if (playerMatch) {
                const player = playerMatch[1]
                return {
                    event_type: 'death_announcement',
                    round_num: round,
                    phase: phase,
                    data: { player, reason: '夜晚死亡' },
                    index: eventIndex
                }
            }
        }

        // Voting
        if (line.includes('投票给') || line.includes('votes for')) {
            const match = line.match(/(\w+)\s*(投票给|votes for)\s*(\w+)/)
            if (match) {
                const voter = match[1]
                const target = match[3]
                return {
                    event_type: 'vote',
                    round_num: round,
                    phase: phase,
                    data: { voter, target },
                    index: eventIndex
                }
            }
        }

        // Role assignments (look for role information)
        const roleMatch = line.match(/(\w+).*?(狼人|村民|预言家|女巫|猎人|守卫|werewolf|villager|seer|witch|hunter|guardian)/)
        if (roleMatch) {
            const player = roleMatch[1]
            let role = roleMatch[2]

            // Normalize role names
            const roleMap = {
                '狼人': 'werewolf',
                '村民': 'villager',
                '预言家': 'seer',
                '女巫': 'witch',
                '猎人': 'hunter',
                '守卫': 'guardian'
            }
            role = roleMap[role] || role

            if (!this.players[player]) {
                this.players[player] = {
                    name: player,
                    role: role,
                    status: 'alive'
                }
            } else {
                this.players[player].role = role
            }
        }

        // Generic event for other lines with content
        if (line.length > 10 && !line.includes('Round') && !line.includes('回合')) {
            return {
                event_type: 'game_event',
                round_num: round,
                phase: phase,
                data: line,
                index: eventIndex
            }
        }

        return null
    }

    updateGameState(event) {
        // Update player states based on events
        if (event.event_type === 'death_announcement' && event.data.player) {
            if (this.players[event.data.player]) {
                this.players[event.data.player].status = 'dead'
            }
        }

        if (event.event_type === 'elimination' && event.data.player) {
            if (this.players[event.data.player]) {
                this.players[event.data.player].status = 'dead'
            }
        }
    }

    getPlayerStateAtEvent(playerName, eventIndex) {
        // Get player state at specific event index
        if (!this.players[playerName]) {
            return { status: 'alive' }
        }

        // Check if player died before this event
        for (let i = 0; i <= eventIndex && i < this.events.length; i++) {
            const event = this.events[i]
            if ((event.event_type === 'death_announcement' || event.event_type === 'elimination')
                && event.data.player === playerName) {
                return { status: 'dead' }
            }
        }

        return { status: 'alive' }
    }
}