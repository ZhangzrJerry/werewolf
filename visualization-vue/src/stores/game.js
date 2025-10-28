import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { gameApi } from '../api/game'

export const useGameStore = defineStore('game', () => {
    // State
    const gameList = ref([])
    const currentGame = ref(null)
    const currentGameFilename = ref(null)
    const gameData = ref(null)
    const gameOverview = ref(null)
    const gameState = ref(null)
    const loading = ref(false)
    const error = ref(null)

    // Getters
    const sortedGameList = computed(() => {
        return gameList.value.sort((a, b) => b.modified - a.modified)
    })

    const isGameLoaded = computed(() => {
        return currentGameFilename.value && gameData.value
    })

    const gameInfo = computed(() => {
        return gameOverview.value?.game_info || null
    })

    const players = computed(() => {
        return gameOverview.value?.players || {}
    })

    const roundSummary = computed(() => {
        return gameOverview.value?.round_summary || []
    })

    const deathTimeline = computed(() => {
        return gameOverview.value?.death_timeline || []
    })

    const votingHistory = computed(() => {
        return gameOverview.value?.voting_history || []
    })

    const specialActions = computed(() => {
        return gameOverview.value?.special_actions || []
    })

    const finalResult = computed(() => {
        return gameOverview.value?.final_result || {}
    })

    const reviewsAndLessons = computed(() => {
        return gameOverview.value?.reviews_and_lessons || {}
    })

    // Actions
    async function fetchGameList() {
        try {
            loading.value = true
            error.value = null
            const response = await gameApi.getGameList()
            gameList.value = response.data
        } catch (err) {
            error.value = err.message || '获取游戏列表失败'
            console.error('获取游戏列表失败:', err)
        } finally {
            loading.value = false
        }
    }

    async function loadGame(filename) {
        try {
            loading.value = true
            error.value = null

            // Load pre-generated static game JSON (frontend-only mode)
            const loadResponse = await gameApi.loadGame(filename)
            currentGameFilename.value = filename
            gameData.value = loadResponse.data

            // The game JSON should contain overview, events, players, etc.
            gameOverview.value = loadResponse.data

            // Initialize client-side interactive state from events array
            const events = loadResponse.data.events || []
            gameState.value = {
                events,
                current_index: 0,
                current_event: events.length > 0 ? toEventDict(events[0]) : null,
            }

        } catch (err) {
            error.value = err.message || '加载游戏失败'
            console.error('加载游戏失败:', err)
        } finally {
            loading.value = false
        }
    }

    async function nextEvent() {
        if (!currentGameFilename.value) return null
        // client-side step forward
        if (!gameState.value || !gameState.value.events) return null
        const idx = Math.min(gameState.value.current_index + 1, gameState.value.events.length - 1)
        gameState.value.current_index = idx
        gameState.value.current_event = toEventDict(gameState.value.events[idx])
        return gameState.value
    }

    async function prevEvent() {
        if (!currentGameFilename.value) return null
        if (!gameState.value || !gameState.value.events) return null
        const idx = Math.max(gameState.value.current_index - 1, 0)
        gameState.value.current_index = idx
        gameState.value.current_event = toEventDict(gameState.value.events[idx])
        return gameState.value
    }

    async function jumpToEvent(eventIndex) {
        if (!currentGameFilename.value) return null
        if (!gameState.value || !gameState.value.events) return null
        const idx = Math.max(0, Math.min(eventIndex, gameState.value.events.length - 1))
        gameState.value.current_index = idx
        gameState.value.current_event = toEventDict(gameState.value.events[idx])
        return gameState.value
    }

    async function resetGame() {
        if (!currentGameFilename.value) return null
        if (!gameState.value || !gameState.value.events) return null
        gameState.value.current_index = 0
        gameState.value.current_event = gameState.value.events.length > 0 ? toEventDict(gameState.value.events[0]) : null
        return gameState.value
    }

    async function refreshGameOverview() {
        if (!currentGameFilename.value) return
        try {
            // load overview from the static game JSON
            const id = currentGameFilename.value.endsWith('.txt') ? currentGameFilename.value.replace(/\.txt$/i, '') : currentGameFilename.value
            const response = await gameApi.getGameOverview(id)
            gameOverview.value = response.data
        } catch (err) {
            error.value = err.message || '刷新游戏概览失败'
            console.error('刷新游戏概览失败:', err)
        }
    }

    function clearCurrentGame() {
        currentGameFilename.value = null
        gameData.value = null
        gameOverview.value = null
        gameState.value = null
        error.value = null
    }

    // Helper to convert an event object to the shape components expect
    function toEventDict(event) {
        if (!event) return null
        return {
            round_num: (event.round_num ?? event.round) || null,
            phase: event.phase || event.phase_name || null,
            event_type: event.type || event.event_type || null,
            data: event.data || event.payload || event,
            timestamp: event.timestamp || null,
        }
    }

    return {
        // State
        gameList,
        currentGame: currentGameFilename,
        currentGameFilename,
        gameData,
        gameOverview,
        gameState,
        loading,
        error,

        // Getters
        sortedGameList,
        isGameLoaded,
        gameInfo,
        players,
        roundSummary,
        deathTimeline,
        votingHistory,
        specialActions,
        finalResult,
        reviewsAndLessons,

        // Actions
        fetchGameList,
        loadGame,
        nextEvent,
        prevEvent,
        jumpToEvent,
        resetGame,
        refreshGameOverview,
        clearCurrentGame
    }
})