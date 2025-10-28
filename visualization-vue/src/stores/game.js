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

            // 加载游戏基本信息
            const loadResponse = await gameApi.loadGame(filename)
            currentGameFilename.value = filename
            gameData.value = loadResponse.data

            // 获取详细的游戏概览
            const overviewResponse = await gameApi.getGameOverview()
            gameOverview.value = overviewResponse.data

            // 获取当前游戏状态
            const stateResponse = await gameApi.getGameState()
            gameState.value = stateResponse.data

        } catch (err) {
            error.value = err.message || '加载游戏失败'
            console.error('加载游戏失败:', err)
        } finally {
            loading.value = false
        }
    }

    async function nextEvent() {
        if (!currentGameFilename.value) return null

        try {
            const response = await gameApi.nextEvent()
            gameState.value = response.data
            return response.data
        } catch (err) {
            error.value = err.message || '移动到下一事件失败'
            console.error('移动到下一事件失败:', err)
            return null
        }
    }

    async function prevEvent() {
        if (!currentGameFilename.value) return null

        try {
            const response = await gameApi.prevEvent()
            gameState.value = response.data
            return response.data
        } catch (err) {
            error.value = err.message || '移动到上一事件失败'
            console.error('移动到上一事件失败:', err)
            return null
        }
    }

    async function jumpToEvent(eventIndex) {
        if (!currentGameFilename.value) return null

        try {
            const response = await gameApi.jumpToEvent(eventIndex)
            gameState.value = response.data
            return response.data
        } catch (err) {
            error.value = err.message || '跳转到事件失败'
            console.error('跳转到事件失败:', err)
            return null
        }
    }

    async function resetGame() {
        if (!currentGameFilename.value) return null

        try {
            const response = await gameApi.resetGame()
            gameState.value = response.data
            return response.data
        } catch (err) {
            error.value = err.message || '重置游戏失败'
            console.error('重置游戏失败:', err)
            return null
        }
    }

    async function refreshGameOverview() {
        if (!currentGameFilename.value) return

        try {
            const response = await gameApi.getGameOverview()
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