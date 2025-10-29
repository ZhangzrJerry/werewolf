<template>
    <div class="werewolf-viewer">
        <!-- Game selector -->
        <div v-if="!currentGame" class="section">
            <h2>选择游戏日志</h2>
            <div v-if="loading" class="loading">加载中...</div>
            <div v-else class="log-list">
                <div v-for="game in games" :key="game.log_file" class="log-item" @click="loadGame(game)">
                    <h3>游戏 #{{ game.game_num }}</h3>
                    <div class="log-meta">
                        <div>时间: {{ formatTime(game.timestamp) }}</div>
                        <div>胜者: {{ game.winner }}</div>
                        <div>回合: {{ game.rounds }}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Game visualization -->
        <div v-if="currentGame" class="game-container">
            <!-- Players panel -->
            <div class="section players-panel">
                <h2>玩家状态</h2>
                <div class="players-circle">
                    <div v-for="player in Object.values(currentGame.players)" :key="player.name"
                        :class="getPlayerCardClass(player)" class="player-card">
                        <div class="player-name">{{ player.name }}</div>
                        <div class="player-role">{{ getRoleTranslation(player.role) }}</div>
                        <div class="player-status">{{ getPlayerStatus(player) }}</div>
                    </div>
                </div>
            </div>

            <!-- Event display -->
            <div class="section event-panel">
                <h2>事件详情</h2>
                <div class="event-info">
                    <div class="phase-indicator">
                        <span>{{ currentPhaseText }}</span>
                    </div>
                    <div class="event-content" v-html="currentEventHtml"></div>
                </div>
            </div>

            <!-- Progress bar -->
            <div class="section progress-section">
                <div class="progress-bar" @click="jumpToPosition">
                    <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
                    <div class="progress-handle" :style="{ left: progressPercent + '%' }"></div>
                </div>
                <div class="progress-info">
                    <span>{{ currentEventIndex }} / {{ totalEvents }}</span>
                </div>
            </div>

            <!-- Control panel -->
            <div class="section control-panel">
                <div class="controls">
                    <button @click="resetGame" class="btn btn-secondary">⏮ 重置</button>
                    <button @click="prevEvent" class="btn btn-secondary">◀ 上一步</button>
                    <button @click="togglePlay" class="btn btn-primary">{{ isPlaying ? '⏸ 暂停' : '▶ 播放' }}</button>
                    <button @click="nextEvent" class="btn btn-secondary">下一步 ▶</button>
                    <button @click="showOverview" class="btn btn-info">📊 全局概览</button>
                    <button @click="backToList" class="btn btn-secondary">🔙 返回选择</button>
                </div>
                <div class="speed-control">
                    <label>播放速度:</label>
                    <select v-model="playSpeed">
                        <option value="2000">慢速 (2s)</option>
                        <option value="1000">中速 (1s)</option>
                        <option value="500">快速 (0.5s)</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- Overview Modal -->
        <div v-if="showOverviewModal" class="modal" @click="closeOverview">
            <div class="modal-content" @click.stop>
                <div class="modal-header">
                    <h2>🎮 游戏全局概览</h2>
                    <span class="close" @click="closeOverview">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="overview-tabs">
                        <button v-for="tab in overviewTabs" :key="tab.id"
                            :class="{ active: currentOverviewTab === tab.id }" @click="currentOverviewTab = tab.id"
                            class="tab-button">
                            {{ tab.label }}
                        </button>
                    </div>
                    <div class="tab-content">
                        <div v-if="currentOverviewTab === 'summary'" class="overview-section">
                            <h3>🏆 游戏结果</h3>
                            <div class="result-summary" v-html="getGameSummary()"></div>
                        </div>
                        <div v-if="currentOverviewTab === 'players'" class="overview-section">
                            <h3>👥 玩家角色与结局</h3>
                            <div class="players-overview" v-html="getPlayersOverview()"></div>
                        </div>
                        <div v-if="currentOverviewTab === 'timeline'" class="overview-section">
                            <h3>💀 死亡时间线</h3>
                            <div class="timeline" v-html="getDeathTimeline()"></div>
                        </div>
                        <div v-if="currentOverviewTab === 'rawlog'" class="overview-section">
                            <h3>📄 完整游戏日志</h3>
                            <pre class="raw-log">{{ rawLog || '正在加载...' }}</pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { getProgress, getRawLog, getParsedForGame } from '../services/trainingService'
import GameLogParser from '../services/gameLogParser'

export default {
    name: 'GameViewer',
    setup() {
        const loading = ref(true)
        const games = ref([])
        const currentGame = ref(null)
        const gameParser = ref(null)
        const currentEventIndex = ref(0)
        const isPlaying = ref(false)
        const playSpeed = ref(1000)
        const playInterval = ref(null)
        const showOverviewModal = ref(false)
        const currentOverviewTab = ref('summary')
        const rawLog = ref('')

        // Role translations
        const roleTranslations = {
            'werewolf': '狼人',
            'villager': '村民',
            'seer': '预言家',
            'witch': '女巫',
            'hunter': '猎人',
            'guardian': '守卫',
            'unknown': '未知'
        }

        // Phase translations
        const phaseTranslations = {
            'night': '夜晚',
            'morning': '早晨',
            'day': '白天',
            'voting': '投票',
            'start': '开始'
        }

        // Event type translations
        const eventTypeTranslations = {
            'phase_start': '阶段开始',
            'guardian_action': '守卫行动',
            'werewolf_target': '狼人选择目标',
            'seer_check': '预言家查验',
            'witch_save': '女巫救人',
            'witch_poison': '女巫用毒',
            'seer_result': '预言家结果',
            'death_announcement': '死亡公告',
            'last_words': '遗言',
            'alive_players': '存活玩家',
            'discussion': '讨论发言',
            'vote': '投票',
            'vote_summary': '投票汇总',
            'elimination': '淘汰',
            'hunter_skill': '猎人技能'
        }

        const overviewTabs = [
            { id: 'summary', label: '📋 游戏总结' },
            { id: 'players', label: '👥 玩家详情' },
            { id: 'timeline', label: '⏰ 死亡时间线' },
            { id: 'rawlog', label: '📄 原始日志' }
        ]

        const totalEvents = computed(() => {
            return gameParser.value?.events?.length || 0
        })

        const progressPercent = computed(() => {
            if (totalEvents.value === 0) return 0
            return (currentEventIndex.value / totalEvents.value) * 100
        })

        const currentEvent = computed(() => {
            if (!gameParser.value || currentEventIndex.value >= totalEvents.value) return null
            return gameParser.value.events[currentEventIndex.value]
        })

        const currentPhaseText = computed(() => {
            if (!currentEvent.value) return '游戏结束'
            return `回合 ${currentEvent.value.round_num} - ${phaseTranslations[currentEvent.value.phase] || currentEvent.value.phase}`
        })

        const currentEventHtml = computed(() => {
            if (!currentEvent.value) return '<p>游戏结束</p>'
            return formatEventHtml(currentEvent.value)
        })

        async function load() {
            loading.value = true
            const p = await getProgress()
            games.value = p.games_history || []
            loading.value = false
        }

        async function loadGame(game) {
            const filename = getFilename(game.log_file)
            rawLog.value = await getRawLog(filename)

            if (rawLog.value && !rawLog.value.startsWith('无法加载') && !rawLog.value.startsWith('加载日志出错')) {
                gameParser.value = new GameLogParser()
                const parsedData = gameParser.value.parseGameLog(rawLog.value)
                currentGame.value = parsedData
                currentEventIndex.value = 0
            } else {
                alert('无法加载游戏日志')
            }
        }

        function getFilename(p) {
            return p.replace(/^.*game_logs[\\\/]/, '')
        }

        function formatTime(ts) {
            try { return new Date(ts).toLocaleString() } catch { return ts }
        }

        function getRoleTranslation(role) {
            return roleTranslations[role] || role
        }

        function getPlayerCardClass(player) {
            const classes = ['player-card']
            const currentState = getCurrentPlayerState(player.name)

            if (currentState?.status === 'dead') {
                classes.push('dead')
            } else {
                classes.push('alive')
            }

            if (currentState?.revealed && player.role === 'werewolf') {
                classes.push('werewolf')
            }

            return classes
        }

        function getPlayerStatus(player) {
            const currentState = getCurrentPlayerState(player.name)
            return currentState?.status === 'alive' ? '存活' : '死亡'
        }

        function getCurrentPlayerState(playerName) {
            // Get current player state based on events up to currentEventIndex
            if (!gameParser.value) return { status: 'alive' }
            return gameParser.value.getPlayerStateAtEvent(playerName, currentEventIndex.value)
        }

        function formatEventHtml(event) {
            let html = `<div class="event-type">${eventTypeTranslations[event.event_type] || event.event_type}</div>`

            switch (event.event_type) {
                case 'phase_start':
                    html += `<p>进入 <strong>${phaseTranslations[event.data.phase]}</strong> 阶段</p>`
                    break

                case 'guardian_action':
                    if (event.data.action === 'no_protection') {
                        html += `<div class="event-data"><p>🛡️ 本局没有守卫，或守卫未行动</p></div>`
                    } else if (event.data.guardian && event.data.protected) {
                        html += `<div class="event-data"><p>🛡️ 守卫 <strong>${event.data.guardian}</strong> 保护了 <strong>${event.data.protected}</strong></p></div>`
                    } else {
                        html += `<div class="event-data"><p>🛡️ 守卫正在行动...</p></div>`
                    }
                    break

                case 'werewolf_target':
                    html += '<div class="event-data"><p><strong>狼人选择目标:</strong></p>'
                    for (const [werewolf, target] of Object.entries(event.data.targets)) {
                        html += `<p>🐺 ${werewolf} → ${target}</p>`
                    }
                    html += '</div>'
                    break

                case 'discussion':
                    html += `<div class="discussion-bubble">`
                    html += `<div class="speaker">💬 ${event.data.speaker}:</div>`
                    html += `<div class="statement">${event.data.statement}</div>`
                    html += `</div>`
                    break

                case 'vote':
                    html += `<div class="event-data"><p>🗳️ <strong>${event.data.voter}</strong> 投票给 <strong>${event.data.target}</strong></p></div>`
                    break

                case 'elimination':
                    html += `<div class="death-announcement">`
                    html += `<p>⚖️ <strong>${event.data.player}</strong> 被投票淘汰</p>`
                    html += `<p>角色: ${roleTranslations[event.data.role] || event.data.role}</p>`
                    html += `</div>`
                    break

                default:
                    html += `<div class="event-data"><pre>${JSON.stringify(event.data, null, 2)}</pre></div>`
            }

            return html
        }

        function resetGame() {
            stopPlaying()
            currentEventIndex.value = 0
        }

        function prevEvent() {
            stopPlaying()
            if (currentEventIndex.value > 0) {
                currentEventIndex.value--
            }
        }

        function nextEvent() {
            stopPlaying()
            if (currentEventIndex.value < totalEvents.value - 1) {
                currentEventIndex.value++
            }
        }

        function togglePlay() {
            if (isPlaying.value) {
                stopPlaying()
            } else {
                startPlaying()
            }
        }

        function startPlaying() {
            if (currentEventIndex.value >= totalEvents.value - 1) return

            isPlaying.value = true
            playInterval.value = setInterval(() => {
                if (currentEventIndex.value < totalEvents.value - 1) {
                    currentEventIndex.value++
                } else {
                    stopPlaying()
                }
            }, playSpeed.value)
        }

        function stopPlaying() {
            isPlaying.value = false
            if (playInterval.value) {
                clearInterval(playInterval.value)
                playInterval.value = null
            }
        }

        function jumpToPosition(event) {
            const rect = event.target.getBoundingClientRect()
            const clickX = event.clientX - rect.left
            const percentage = clickX / rect.width

            stopPlaying()
            currentEventIndex.value = Math.round(percentage * (totalEvents.value - 1))
        }

        function backToList() {
            stopPlaying()
            currentGame.value = null
            gameParser.value = null
            currentEventIndex.value = 0
            rawLog.value = ''
        }

        function showOverview() {
            showOverviewModal.value = true
        }

        function closeOverview() {
            showOverviewModal.value = false
        }

        function getGameSummary() {
            if (!currentGame.value) return ''
            const info = currentGame.value.game_info || {}
            return `
        <p><strong>胜利方:</strong> ${info.winner || '未知'}</p>
        <p><strong>回合数:</strong> ${info.rounds_played || '未知'}</p>
        <p><strong>游戏类型:</strong> ${info.game_type || '标准狼人杀'}</p>
      `
        }

        function getPlayersOverview() {
            if (!currentGame.value?.players) return ''
            return Object.values(currentGame.value.players).map(player => {
                const finalState = getCurrentPlayerState(player.name)
                return `
          <div class="player-overview">
            <strong>${player.name}</strong> - ${getRoleTranslation(player.role)} 
            (${finalState?.status === 'alive' ? '存活' : '死亡'})
          </div>
        `
            }).join('')
        }

        function getDeathTimeline() {
            // Simple death timeline - would need more complex logic for detailed timeline
            return '<p>死亡时间线功能开发中...</p>'
        }

        onMounted(load)

        onUnmounted(() => {
            stopPlaying()
        })

        return {
            loading,
            games,
            currentGame,
            currentEventIndex,
            totalEvents,
            progressPercent,
            currentPhaseText,
            currentEventHtml,
            isPlaying,
            playSpeed,
            showOverviewModal,
            currentOverviewTab,
            overviewTabs,
            rawLog,
            loadGame,
            formatTime,
            getRoleTranslation,
            getPlayerCardClass,
            getPlayerStatus,
            resetGame,
            prevEvent,
            nextEvent,
            togglePlay,
            jumpToPosition,
            backToList,
            showOverview,
            closeOverview,
            getGameSummary,
            getPlayersOverview,
            getDeathTimeline
        }
    }
}
</script>

<style scoped>
.werewolf-viewer {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.section {
    margin-bottom: 20px;
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
}

.loading {
    text-align: center;
    padding: 40px;
    color: #666;
}

.log-list {
    display: grid;
    gap: 16px;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.log-item {
    background: white;
    padding: 16px;
    border-radius: 8px;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.2s;
}

.log-item:hover {
    border-color: #007bff;
    transform: translateY(-2px);
}

.log-meta {
    margin-top: 8px;
    font-size: 14px;
    color: #666;
}

.players-circle {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    justify-content: center;
}

.player-card {
    background: white;
    padding: 16px;
    border-radius: 8px;
    text-align: center;
    min-width: 120px;
    border: 2px solid #ddd;
}

.player-card.alive {
    border-color: #28a745;
}

.player-card.dead {
    border-color: #dc3545;
    opacity: 0.7;
}

.player-card.werewolf {
    border-color: #6f42c1;
}

.event-content {
    background: white;
    padding: 20px;
    border-radius: 8px;
    min-height: 200px;
}

.discussion-bubble {
    background: #e9ecef;
    padding: 12px;
    border-radius: 8px;
    margin: 8px 0;
}

.speaker {
    font-weight: bold;
    color: #007bff;
    margin-bottom: 4px;
}

.progress-bar {
    position: relative;
    height: 20px;
    background: #e9ecef;
    border-radius: 10px;
    cursor: pointer;
    margin: 16px 0;
}

.progress-fill {
    height: 100%;
    background: #007bff;
    border-radius: 10px;
    transition: width 0.3s;
}

.progress-handle {
    position: absolute;
    top: -5px;
    width: 30px;
    height: 30px;
    background: #007bff;
    border-radius: 50%;
    transform: translateX(-50%);
    cursor: pointer;
}

.controls {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

.btn-primary {
    background: #007bff;
    color: white;
}

.btn-secondary {
    background: #6c757d;
    color: white;
}

.btn-info {
    background: #17a2b8;
    color: white;
}

.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    border-radius: 8px;
    max-width: 90vw;
    max-height: 90vh;
    overflow: auto;
}

.modal-header {
    padding: 20px;
    border-bottom: 1px solid #dee2e6;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.close {
    font-size: 24px;
    cursor: pointer;
}

.overview-tabs {
    display: flex;
    border-bottom: 1px solid #dee2e6;
}

.tab-button {
    padding: 12px 16px;
    border: none;
    background: none;
    cursor: pointer;
}

.tab-button.active {
    background: #007bff;
    color: white;
}

.tab-content {
    padding: 20px;
}

.raw-log {
    max-height: 400px;
    overflow: auto;
    background: #f8f9fa;
    padding: 16px;
    font-size: 12px;
}
</style>