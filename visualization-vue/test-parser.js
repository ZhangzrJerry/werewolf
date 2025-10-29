// Simple test for game log parser
import GameLogParser from './src/services/gameLogParser.js'
import fs from 'fs'

const logPath = 'd:/Projects/werewolf/.training/game_logs/werewolf_game_20251028_160800_cfb7553b.txt'
const logText = fs.readFileSync(logPath, 'utf-8')

const parser = new GameLogParser()
const result = parser.parseGameLog(logText)

console.log('=== Game Info ===')
console.log('Game Type:', result.game_info.game_type)
console.log('Player Names:', result.game_info.player_names)
console.log('Werewolf Team:', result.game_info.werewolf_team)

console.log('\n=== Players ===')
Object.values(result.players).forEach(p => {
    console.log(`${p.name}: ${p.role} (${p.status})`)
})

console.log('\n=== Events Count ===')
console.log('Total Events:', result.events.length)
if (result.events.length > 0) {
    console.log('First 5 events:')
    result.events.slice(0, 5).forEach((e, i) => {
        console.log(`${i}: ${e.event_type} - ${JSON.stringify(e.data)}`)
    })
}
