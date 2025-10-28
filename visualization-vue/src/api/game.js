// This module provides a frontend-only data loader that reads pre-generated
// static artifacts under the `/werewolf` path. This lets the Vue app run
// without depending on the Flask backend. The build/deploy process must copy
// `.training` contents into `werewolf/` (use scripts/copy-training-data.js).

const BASE = '/werewolf'

function handleFetch(response) {
    if (!response.ok) throw new Error(`${response.status}: ${response.statusText}`)
    return response.json()
}

export const gameApi = {
    // Try to load a prebuilt index of game logs at /werewolf/game_logs/index.json
    async getGameList() {
        // fallback order: /werewolf/game_logs/index.json -> /werewolf/games.json
        try {
            const r = await fetch(`${BASE}/game_logs/index.json`)
            return { data: await handleFetch(r) }
        } catch (e) {
            const r2 = await fetch(`${BASE}/games.json`)
            return { data: await handleFetch(r2) }
        }
    },

    // Load a pre-parsed game JSON. The frontend expects files like
    // /werewolf/game/<gameId>.json (gameId = filename without extension).
    async loadGame(filename) {
        const id = filename.endsWith('.txt') ? filename.replace(/\.txt$/i, '') : filename
        const url = `${BASE}/game/${id}.json`
        const r = await fetch(url)
        if (!r.ok) {
            // try legacy location
            const alt = `${BASE}/game_data/${id}.json`
            const r2 = await fetch(alt)
            if (!r2.ok) throw new Error(`Failed to load game ${id}`)
            return { data: await r2.json() }
        }
        return { data: await r.json() }
    },

    // Static mode: game overview is included in the same JSON as the game data
    async getGameOverview(gameId) {
        const id = gameId || ''
        const url = id ? `${BASE}/game/${id}.json` : `${BASE}/overview.json`
        const r = await fetch(url)
        return { data: await handleFetch(r) }
    },

    // The interactive state (next/prev/jump/reset) is implemented client-side
    // in the Pinia store when running without Flask. Keep these as no-ops for
    // compatibility; the store will manage state locally.
    async getGameState() { return { data: null } },
    async nextEvent() { return { data: null } },
    async prevEvent() { return { data: null } },
    async jumpToEvent() { return { data: null } },
    async resetGame() { return { data: null } },

    // Additional static resources
    async getAllGames() { const r = await fetch(`${BASE}/games.json`); return { data: await handleFetch(r) } },
    async getGameData(gameId) { const r = await fetch(`${BASE}/game/${gameId}.json`); return { data: await handleFetch(r) } },
    async getReviews() { const r = await fetch(`${BASE}/reviews/index.json`); return { data: await handleFetch(r) } },
    async getDocumentation() { const r = await fetch(`${BASE}/doc.json`); return { data: await handleFetch(r) } },
    async getAsset(filename) { const r = await fetch(`${BASE}/assets/${filename}`); if (!r.ok) throw new Error('Asset not found'); return { data: await r.blob() } }
}