import api from './index'

export const gameApi = {
    // 获取游戏日志列表 - 对应 Flask 的 /api/logs
    getGameList() {
        return api.get('/logs')
    },

    // 加载特定游戏 - 对应 Flask 的 /api/load/<filename>
    loadGame(filename) {
        return api.get(`/load/${filename}`)
    },

    // 获取当前游戏状态 - 对应 Flask 的 /api/state
    getGameState() {
        return api.get('/state')
    },

    // 获取游戏概览 - 对应 Flask 的 /api/overview
    getGameOverview() {
        return api.get('/overview')
    },

    // 移动到下一个事件 - 对应 Flask 的 /api/next
    nextEvent() {
        return api.get('/next')
    },

    // 移动到上一个事件 - 对应 Flask 的 /api/prev
    prevEvent() {
        return api.get('/prev')
    },

    // 跳转到特定事件 - 对应 Flask 的 /api/jump/<int:event_index>
    jumpToEvent(eventIndex) {
        return api.get(`/jump/${eventIndex}`)
    },

    // 重置到开始 - 对应 Flask 的 /api/reset
    resetGame() {
        return api.get('/reset')
    },

    // 获取所有游戏（用于静态站点） - 对应 Flask 的 /api/games
    getAllGames() {
        return api.get('/games')
    },

    // 获取特定游戏数据（用于静态站点） - 对应 Flask 的 /api/game/<game_id>
    getGameData(gameId) {
        return api.get(`/game/${gameId}`)
    },

    // 获取所有reviews - 对应 Flask 的 /api/reviews
    getReviews() {
        return api.get('/reviews')
    },

    // 获取文档 - 对应 Flask 的 /api/doc
    getDocumentation() {
        return api.get('/doc')
    },

    // 获取静态资源 - 对应 Flask 的 /api/assets/<path:filename>
    getAsset(filename) {
        return api.get(`/assets/${filename}`)
    }
}