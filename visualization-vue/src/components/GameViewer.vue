<template>
    <div class="werewolf-viewer">
        <!-- Game selector -->
        <div v-if="!currentGame" class="section">
            <h2>🎮 选择游戏日志</h2>
            <div v-if="loading" class="loading">加载中...</div>
            <div v-else class="log-list">
                <div v-for="game in games" :key="game.log_file" class="log-item" @click="loadGame(game)">
                    <div class="log-header">
                        <h3>游戏 #{{ game.game_num }}</h3>
                        <span class="winner-badge" :class="game.winner">{{ game.winner === 'werewolves' ? '🐺 狼人' :
                            game.winner === 'villagers' ? '👥 村民' : game.winner }}</span>
                    </div>
                    <div class="log-meta">
                        <div class="meta-item">⏱️ {{ formatTime(game.timestamp) }}</div>
                        <div class="meta-item">🔄 {{ game.rounds }} 回合</div>
                        <div class="meta-item">👥 {{ game.player_count || '?' }} 玩家</div>
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
                            <div class="result-summary" v-html="getGameSummary()"></div>
                        </div>
                        <!-- players tab removed per request -->
                        <div v-if="currentOverviewTab === 'votes'" class="overview-section">
                            <div class="votes-overview" v-html="getVotesOverview()"></div>
                        </div>
                        <div v-if="currentOverviewTab === 'review'" class="overview-section">
                            <div class="review-overview" v-html="getGameReview()"></div>
                        </div>
                        <div v-if="currentOverviewTab === 'rawlog'" class="overview-section">
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
import { getProgress, getRawLog, getParsedForGame, findReviewsForGame } from '../services/trainingService'
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
        const reviewFolder = ref(null)
        const overallReview = ref('')
        const perPlayerReviews = ref({})

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
            { id: 'votes', label: '🗳️ 投票记录' },
            { id: 'review', label: '⭐ 游戏评价' },
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
                console.log('Game loaded:', parsedData)
                console.log('Players:', parsedData.players)
                console.log('Events:', parsedData.events)
                // attempt to load reviews referenced in the raw log
                try {
                    await loadReviews(filename)
                } catch (e) {
                    console.warn('Failed to load reviews for', filename, e)
                }
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

            // Add role-based classes for styling
            if (player.role === 'werewolf') {
                classes.push('role-werewolf')
            } else if (player.role === 'villager') {
                classes.push('role-villager')
            } else if (player.role === 'seer') {
                classes.push('role-seer')
            } else if (player.role === 'witch') {
                classes.push('role-witch')
            } else if (player.role === 'hunter') {
                classes.push('role-hunter')
            } else if (player.role === 'guardian') {
                classes.push('role-guardian')
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
            if (!gameParser.value.getPlayerStateAtEvent) return { status: 'alive' }

            try {
                return gameParser.value.getPlayerStateAtEvent(playerName, currentEventIndex.value)
            } catch (e) {
                console.error('Error getting player state:', e)
                return { status: 'alive' }
            }
        }

        function getFinalPlayerState(playerName) {
            // Get final player state at game end
            if (!gameParser.value) return { status: 'alive' }
            if (!gameParser.value.getPlayerStateAtEvent) return { status: 'alive' }

            try {
                const totalEvents = gameParser.value.events?.length || 0
                return gameParser.value.getPlayerStateAtEvent(playerName, totalEvents)
            } catch (e) {
                console.error('Error getting final player state:', e)
                return { status: 'alive' }
            }
        }

        function formatEventHtml(event) {
            let html = `<div class="event-type">${eventTypeTranslations[event.event_type] || event.event_type}</div>`

            switch (event.event_type) {
                case 'phase_start':
                    html += `<p>进入 <strong>${phaseTranslations[event.data.phase] || event.data.phase}</strong> 阶段</p>`
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
                    html += '<div class="event-data"><p><strong>🐺 狼人选择目标:</strong></p>'
                    if (event.data.targets && typeof event.data.targets === 'object') {
                        for (const [werewolf, target] of Object.entries(event.data.targets)) {
                            html += `<p>  ${werewolf} → ${target}</p>`
                        }
                    }
                    html += '</div>'
                    break

                case 'seer_check':
                    html += `<div class="event-data"><p>🔮 预言家 <strong>${event.data.seer}</strong> 查验了 <strong>${event.data.target}</strong></p></div>`
                    break

                case 'seer_result':
                    html += `<div class="event-data"><p>🔮 预言家 <strong>${event.data.seer}</strong> 得知 <strong>${event.data.target}</strong> 是 <strong>${event.data.result === 'werewolf' ? '狼人' : '村民'}</strong></p></div>`
                    break

                case 'witch_save':
                    if (event.data.saved) {
                        html += `<div class="event-data"><p>💊 女巫 <strong>${event.data.witch}</strong> 救了 <strong>${event.data.target}</strong></p></div>`
                    } else {
                        html += `<div class="event-data"><p>💊 女巫 <strong>${event.data.witch}</strong> 没有救人</p></div>`
                    }
                    break

                case 'witch_poison':
                    if (event.data.used) {
                        html += `<div class="event-data"><p>☠️ 女巫 <strong>${event.data.witch}</strong> 对 <strong>${event.data.target}</strong> 使用了毒药</p></div>`
                    } else {
                        html += `<div class="event-data"><p>☠️ 女巫 <strong>${event.data.witch}</strong> 没有使用毒药</p></div>`
                    }
                    break

                case 'death_announcement':
                    html += `<div class="death-announcement"><p>💀 <strong>${event.data.player}</strong> 在夜晚死亡</p></div>`
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
                    if (event.data.role) {
                        html += `<p>角色: ${roleTranslations[event.data.role] || event.data.role}</p>`
                    }
                    html += `</div>`
                    break

                case 'hunter_skill':
                    html += `<div class="death-announcement"><p>🏹 猎人 <strong>${event.data.hunter}</strong> 射杀了 <strong>${event.data.target}</strong></p></div>`
                    break

                case 'safe_night':
                    html += `<div class="event-data"><p>✨ ${event.data.message}</p></div>`
                    break

                case 'game_event':
                    html += `<div class="event-data"><p>${event.data}</p></div>`
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
            if (!currentGame.value) return '<p>没有游戏数据</p>'
            const game = currentGame.value
            const info = game.game_info || {}
            const playersObj = game.players || {}
            const players = Object.values(playersObj)

            const escapeHtml = s => s ? String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') : ''

            // build werewolf team if info missing
            let werewolfTeam = info.werewolf_team || []
            if ((!werewolfTeam || werewolfTeam.length === 0) && players.length > 0) {
                werewolfTeam = players.filter(p => p.role === 'werewolf').map(p => p.name)
            }

            // role counts
            const roleCounts = {}
            players.forEach(p => roleCounts[p.role] = (roleCounts[p.role] || 0) + 1)

            // Flask-style result summary with cards
            let html = '<div class="overview-section"><h3>🏆 游戏结果</h3><div class="result-summary">'

            // Winner card (with Flask-style gradient)
            const winnerText = info.winner === 'werewolves' ? '🐺 狼人阵营' : info.winner === 'villagers' ? '👥 村民阵营' : escapeHtml(info.winner || '未知')
            const winnerClass = info.winner === 'werewolves' ? 'loser' : info.winner === 'villagers' ? 'winner' : ''
            html += `<div class="result-card ${winnerClass}"><div class="title">胜利方</div><div class="value">${winnerText}</div></div>`

            // Rounds card
            html += `<div class="result-card"><div class="title">回合数</div><div class="value">${game.rounds || info.rounds_played || '—'}</div></div>`

            // Total players card
            html += `<div class="result-card"><div class="title">玩家总数</div><div class="value">${players.length}</div></div>`

            // Werewolf count card
            const werewolfCount = players.filter(p => p.role === 'werewolf').length
            html += `<div class="result-card"><div class="title">狼人数量</div><div class="value">${werewolfCount}</div></div>`

            html += '</div></div>'

            // Stats grid (Flask-style)
            html += '<div class="overview-section"><h3>📊 数据统计</h3><div class="stats-grid">'

            // Game type stat
            html += `<div class="stat-item"><div class="label">游戏类型</div><div class="value">${escapeHtml(info.game_type || '标准狼人杀')}</div></div>`

            // Werewolf team stat
            if (werewolfTeam && werewolfTeam.length) {
                html += `<div class="stat-item"><div class="label">狼人阵营</div><div class="value">${werewolfTeam.map(escapeHtml).join(', ')}</div></div>`
            }

            // Role distribution stats
            Object.entries(roleCounts).forEach(([role, count]) => {
                if (role !== 'unknown') {
                    html += `<div class="stat-item"><div class="label">${escapeHtml(getRoleTranslation(role))}</div><div class="value">${count}人</div></div>`
                }
            })

            html += '</div></div>'

            return html
        }

        // players overview removed — no longer used

        async function loadReviews(filename) {
            overallReview.value = ''
            perPlayerReviews.value = {}
            reviewFolder.value = null

            // Try to find the review folder path from the raw log
            try {
                if (rawLog.value) {
                    const m = rawLog.value.match(/Reviews and lessons saved to:\s*(.+)/i)
                    if (m && m[1]) {
                        const fullPath = m[1].trim()
                        const parts = fullPath.split(/[/\\]+/)
                        const folderName = parts.pop()
                        if (folderName) {
                            reviewFolder.value = folderName
                        }
                    }
                }

                // If we have a folder name, try fetching overall and per-player reviews
                if (reviewFolder.value) {
                    const baseUrl = `/.training/reviews/${reviewFolder.value}`
                    try {
                        const r = await fetch(`${baseUrl}/overall.txt`)
                        if (r.ok) overallReview.value = await r.text()
                    } catch (e) { /* ignore */ }

                    const players = currentGame.value?.players ? Object.values(currentGame.value.players).map(p => p.name) : []
                    for (const name of players) {
                        try {
                            const purl = `${baseUrl}/${encodeURIComponent(name)}_review.txt`
                            const pr = await fetch(purl)
                            if (pr.ok) perPlayerReviews.value[name] = await pr.text()
                        } catch (e) { /* ignore */ }
                    }
                    return
                }

                // fallback: try heuristic search via service
                const found = await findReviewsForGame(filename).catch(() => [])
                if (found && found.length > 0) {
                    // try to pick an overall.txt or first text file
                    for (const url of found) {
                        try {
                            const r = await fetch(url)
                            if (r.ok) {
                                const text = await r.text()
                                // use as overall if it looks like overall
                                overallReview.value = text
                                break
                            }
                        } catch (e) { }
                    }
                }
            } catch (e) {
                console.warn('loadReviews error', e)
            }
        }

        function getVotesOverview() {
            try {
                const escapeHtml = s => s ? String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') : ''

                const allEvents = gameParser.value?.events || []
                const votes = allEvents.filter(e => e.event_type === 'vote')

                if (!votes || votes.length === 0) {
                    return '<div class="overview-section"><h3>🗳️ 投票记录</h3><p style="padding: 20px;">暂无投票记录</p></div>'
                }

                // Group votes by round
                const votesByRound = {}
                votes.forEach(vote => {
                    const round = vote.round_num
                    if (!votesByRound[round]) votesByRound[round] = []
                    votesByRound[round].push(vote)
                })

                const roundNumbers = Object.keys(votesByRound).sort((a, b) => parseInt(a) - parseInt(b))

                // Flask-style voting history layout
                let html = '<div class="overview-section"><h3>🗳️ 投票记录</h3><div class="voting-history">'

                roundNumbers.forEach(round => {
                    const roundVotes = votesByRound[round]

                    // Flask-style voting round with header and vote list
                    html += `<div class="voting-round"><div class="voting-round-header">第 ${escapeHtml(round)} 轮投票</div>`
                    html += '<div class="votes-list">'

                    // List each vote (Flask-style voter → target format)
                    roundVotes.forEach(v => {
                        const voter = escapeHtml(v.data?.voter || '?')
                        const target = escapeHtml(v.data?.target || '?')
                        html += `<div class="vote-item"><span class="voter">${voter}</span><span class="vote-arrow">→</span><span class="target">${target}</span></div>`
                    })

                    html += '</div>'  // end votes-list

                    // Vote count summary (Flask-style)
                    const voteCount = {}
                    roundVotes.forEach(v => {
                        const target = v.data?.target
                        if (target) voteCount[target] = (voteCount[target] || 0) + 1
                    })

                    const sorted = Object.entries(voteCount).sort((a, b) => b[1] - a[1])
                    if (sorted.length > 0) {
                        html += '<div style="padding: 10px 20px; background: #f0f0f0; border-top: 1px solid #ddd; font-size: 0.9em; color: #666;"><strong>投票统计:</strong> '
                        html += sorted.map(([target, count]) => {
                            const emoji = count === Math.max(...sorted.map(s => s[1])) ? '⭐' : ''
                            return `${emoji} ${escapeHtml(target)}: <strong>${count}</strong>票`
                        }).join(' | ')
                        html += '</div>'
                    }

                    // Show elimination result if exists
                    const eliminationEvent = allEvents.find(ev => ev.event_type === 'elimination' && String(ev.round_num) === String(round))
                    if (eliminationEvent && eliminationEvent.data && eliminationEvent.data.player) {
                        const elimRole = eliminationEvent.data.role ? ` (${escapeHtml(getRoleTranslation(eliminationEvent.data.role))})` : ''
                        html += `<div style="padding: 10px 20px; background: #ffe5e5; border-top: 1px solid #ffcccc; color: #d32f2f; font-weight: bold;">⚖️ 淘汰: ${escapeHtml(eliminationEvent.data.player)}${elimRole}</div>`
                    }

                    html += '</div>'  // end voting-round
                })

                html += '</div></div>'  // end voting-history & overview-section
                return html
            } catch (error) {
                console.error('Error in getVotesOverview:', error)
                return '<p style="color: red;">获取投票记录出错</p>'
            }
        }

        function getGameReview() {
            try {
                const escapeHtml = (s) => s ? String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') : ''

                if (overallReview.value || Object.keys(perPlayerReviews.value || {}).length > 0) {
                    let html = '<div class="review-content">'

                    if (overallReview.value) {
                        const out = escapeHtml(overallReview.value).replace(/\n/g, '<br>')
                        html += `<div class="review-section"><h4>📋 Overall Review</h4><div class="review-text">${out}</div></div>`
                    }

                    const players = Object.keys(perPlayerReviews.value || {})
                    if (players.length > 0) {
                        html += '<div class="review-section"><h4>🎯 按玩家评价</h4>'
                        players.forEach(name => {
                            const txt = perPlayerReviews.value[name] || ''
                            const pOut = escapeHtml(txt).replace(/\n/g, '<br>')
                            html += `<div class="review-item"><h5>${escapeHtml(name)}</h5><div class="review-text">${pOut}</div></div>`
                        })
                        html += '</div>'
                    }

                    if (reviewFolder.value) {
                        html += `<div class="review-section"><small>Reviews folder: /.training/reviews/${escapeHtml(reviewFolder.value)}</small></div>`
                    }

                    html += '</div>'
                    return html
                }

                return '<p style="padding: 20px;">暂无评价文件 (未在日志中找到 review 目录)</p>'
            } catch (error) {
                console.error('Error in getGameReview:', error)
                return '<p style="color: red;">获取游戏评价出错</p>'
            }
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
            // getPlayersOverview removed
            getVotesOverview,
            getGameReview
        }
    }
}
</script>

<style scoped>
.werewolf-viewer {
    width: 100%;
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
    transition: all 0.3s ease;
}

.player-card.alive {
    border-color: #28a745;
}

.player-card.dead {
    border-color: #dc3545;
    opacity: 0.7;
}

.player-name {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
}

.player-role {
    font-size: 12px;
    color: #666;
    margin-bottom: 8px;
}

.player-status {
    font-size: 12px;
    color: #999;
}

/* 三种颜色方案：狼人(淡紫色)、村民(淡绿色)、神职者(淡金色) */
.player-card.role-werewolf {
    background: white;
    color: #5b21b6;
    border: 2px solid #ddd6fe;
}

.player-card.role-werewolf .player-name {
    font-weight: bold;
    color: #5b21b6;
}

.player-card.role-werewolf .player-role {
    font-weight: bold;
    color: #5b21b6;
}

.player-card.role-werewolf .player-status {
    color: #5b21b6;
}

/* 村民及所有非特殊职业 */
.player-card.role-villager {
    background: white;
    color: #065f46;
    border: 2px solid #a7f3d0;
}

.player-card.role-villager .player-name {
    font-weight: bold;
    color: #065f46;
}

.player-card.role-villager .player-role {
    color: #065f46;
}

.player-card.role-villager .player-status {
    color: #065f46;
}

/* 神职者(预言家、女巫、猎人、守卫) */
.player-card.role-seer,
.player-card.role-witch,
.player-card.role-hunter,
.player-card.role-guardian {
    background: white;
    color: #92400e;
    border: 2px solid #fde68a;
}

.player-card.role-seer .player-name,
.player-card.role-witch .player-name,
.player-card.role-hunter .player-name,
.player-card.role-guardian .player-name {
    font-weight: bold;
    color: #92400e;
}

.player-card.role-seer .player-role,
.player-card.role-witch .player-role,
.player-card.role-hunter .player-role,
.player-card.role-guardian .player-role {
    font-weight: bold;
    color: #92400e;
}

.player-card.role-seer .player-status,
.player-card.role-witch .player-status,
.player-card.role-hunter .player-status,
.player-card.role-guardian .player-status {
    color: #92400e;
}

/* 死亡玩家 - 彩色背景 + 白文字 */
.player-card.dead.role-werewolf {
    background: #ede9fe;
    color: white;
    border: 2px solid #ddd6fe;
    opacity: 1;
}

.player-card.dead.role-werewolf .player-name,
.player-card.dead.role-werewolf .player-role,
.player-card.dead.role-werewolf .player-status {
    color: white;
}

.player-card.dead.role-villager {
    background: #d1fae5;
    color: white;
    border: 2px solid #a7f3d0;
    opacity: 1;
}

.player-card.dead.role-villager .player-name,
.player-card.dead.role-villager .player-role,
.player-card.dead.role-villager .player-status {
    color: white;
}

.player-card.dead.role-seer,
.player-card.dead.role-witch,
.player-card.dead.role-hunter,
.player-card.dead.role-guardian {
    background: #fef3c7;
    color: white;
    border: 2px solid #fde68a;
    opacity: 1;
}

.player-card.dead.role-seer .player-name,
.player-card.dead.role-seer .player-role,
.player-card.dead.role-seer .player-status,
.player-card.dead.role-witch .player-name,
.player-card.dead.role-witch .player-role,
.player-card.dead.role-witch .player-status,
.player-card.dead.role-hunter .player-name,
.player-card.dead.role-hunter .player-role,
.player-card.dead.role-hunter .player-status,
.player-card.dead.role-guardian .player-name,
.player-card.dead.role-guardian .player-role,
.player-card.dead.role-guardian .player-status {
    color: white;
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
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.modal-header {
    padding: 20px;
    border-bottom: 1px solid #dee2e6;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
}

.modal-body {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    flex: 1;
    /* allow flex children to shrink properly in some browsers */
    min-height: 0;
}

.overview-tabs {
    display: flex;
    border-bottom: 1px solid #dee2e6;
    flex-shrink: 0;
    background: white;
}

.tab-button {
    padding: 12px 16px;
    border: none;
    background: none;
    cursor: pointer;
    white-space: nowrap;
}

.tab-button.active {
    background: #007bff;
    color: white;
}

/* .close {
    font-size: 24px;
    cursor: pointer;
    color: #666;
}*/

.close:hover {
    color: #313131;
}

.tab-content {
    padding: 20px;
    overflow-y: auto;
    flex: 1;
}

.raw-log {
    max-height: 400px;
    overflow: auto;
    background: #f8f9fa;
    color: #333;
    padding: 16px;
    font-size: 12px;
}

/* Enhanced styles for game list */
.log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.winner-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
    color: white;
}

.winner-badge.werewolves {
    background: #dc3545;
}

.winner-badge.villagers {
    background: #28a745;
}

.meta-item {
    display: inline-block;
    margin-right: 16px;
    font-size: 13px;
    color: #666;
}

/* Game summary styles */
.game-summary {
    background: #f8f9fa;
    padding: 16px;
    border-radius: 8px;
}

.game-summary p {
    margin: 8px 0;
}

.game-summary ul {
    margin: 8px 0 8px 20px;
}

.game-summary li {
    margin: 4px 0;
}

/* Players overview styles */
.players-overview {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 12px;
}

/* Summary grid and roster */
.game-summary-grid {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 16px;
}

.summary-left {
    min-width: 0;
}

.summary-right .roster {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.player-badge {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px;
    border-radius: 6px;
    background: #fff;
    border: 1px solid #eee;
}

.player-badge.dead {
    opacity: 0.6;
}

.player-badge .role {
    color: #666;
    margin-left: 8px;
    font-size: 13px
}

.player-badge .status {
    margin-left: 12px
}

.player-overview-card {
    background: white;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    padding: 12px;
    transition: all 0.3s ease;
}

.player-overview-card:hover {
    border-color: #007bff;
    box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
}

.player-info {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.status-icon {
    font-size: 20px;
}

.role-badge {
    background: #e9ecef;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    color: #495057;
}

.player-status {
    font-size: 13px;
    color: #666;
    margin-top: 4px;
}

.death-round {
    font-size: 12px;
    color: #999;
    margin-top: 4px;
}

/* Event detail styles */
.event-type {
    font-weight: bold;
    color: #007bff;
    margin-bottom: 8px;
    font-size: 16px;
}

.event-data {
    padding: 12px;
    background: #f8f9fa;
    border-left: 4px solid #007bff;
    border-radius: 4px;
}

.event-data p {
    margin: 4px 0;
    font-size: 14px;
}

.discussion-bubble {
    background: #e3f2fd;
    padding: 12px;
    border-radius: 8px;
    margin: 8px 0;
}

.speaker {
    font-weight: bold;
    color: #1976d2;
    margin-bottom: 4px;
}

.statement {
    color: #333;
    font-style: italic;
}

.death-announcement {
    background: #ffebee;
    padding: 12px;
    border-radius: 8px;
    border-left: 4px solid #d32f2f;
}

.death-announcement p {
    margin: 4px 0;
}

/* Voting styles */
.votes-table {
    margin-top: 12px;
}

.vote-round {
    background: #f8f9fa;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 12px;
}

.vote-round h4 {
    margin-top: 0;
    color: #007bff;
}

.vote-details {
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
}

.vote-details th,
.vote-details td {
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
}

.vote-details th {
    background: #e3f2fd;
    font-weight: bold;
    color: #1976d2;
}

.vote-grid {
    display: flex;
    gap: 12px;
    align-items: flex-start;
}

.vote-summary {
    min-width: 140px;
    background: #fff;
    padding: 8px;
    border-radius: 6px;
    border: 1px solid #eee;
}

.vote-count {
    margin: 4px 0;
    font-weight: 600
}

.vote-details tr:hover {
    background: #f0f0f0;
}

/* Review styles */
.review-content {
    margin-top: 12px;
}

.review-section {
    background: #f8f9fa;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 16px;
}

.review-section h4 {
    margin-top: 0;
    color: #333;
    border-bottom: 2px solid #007bff;
    padding-bottom: 8px;
}

.review-section p {
    margin: 8px 0;
    line-height: 1.6;
}

.player-ratings {
    display: grid;

    .review-text {
        white-space: pre-wrap;
        word-break: break-word;
        overflow-wrap: anywhere;
        font-family: system-ui, "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        background: #fafafa;
        padding: 10px;
        border-radius: 6px;
    }

    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    margin-top: 12px;
}

.rating-item {
    background: white;
    padding: 12px;
    border-radius: 6px;
    border-left: 4px solid #007bff;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.player-name {
    font-weight: bold;
    color: #333;
}

.player-role {
    font-size: 12px;
    color: #666;
}

.player-result {
    font-size: 12px;
    color: #28a745;
}

/* Vote table styles */
.vote-round {
    margin-bottom: 20px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
}

.vote-round h4 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 16px;
}

.vote-details {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 12px;
    background: white;
    border-radius: 6px;
    overflow: hidden;
}

.vote-details thead {
    background: #e9ecef;
}

.vote-details th,
.vote-details td {
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
    font-size: 14px;
}

.vote-details tr:hover {
    background: #f8f9fa;
}

.vote-summary {
    background: white;
    padding: 12px;
    border-radius: 6px;
    border-left: 3px solid #ffc107;
}

.vote-summary h5 {
    margin: 0 0 8px 0;
    color: #666;
    font-size: 13px;
}

.vote-count {
    padding: 6px 0;
    color: #333;
    font-size: 14px;
}

/* Game review styles */
.game-info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin: 12px 0;
}

.info-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 6px;
}

.info-label {
    font-weight: bold;
    color: #666;
    font-size: 12px;
}

.info-value {
    color: #333;
    font-size: 16px;
}

/* Role group styles */
.role-group {
    margin-bottom: 16px;
    padding: 12px;
    background: white;
    border-radius: 6px;
    border-left: 3px solid #007bff;
}

.role-group h5 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 14px;
}

.status-icon {
    margin-right: 4px;
    font-size: 16px;
}

/* Evaluation section */
.evaluation {
    background: white;
    padding: 16px;
    border-radius: 6px;
    line-height: 1.8;
}

.evaluation p {
    margin: 10px 0;
    color: #333;
    font-size: 14px;
}

/* Result-summary (compact) */
.result-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.result-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
}

.result-card .title {
    font-size: 0.9em;
    opacity: 0.9;
    margin-bottom: 10px;
}

.result-card .value {
    font-size: 2em;
    font-weight: bold;
}

.result-card.winner {
    background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
}

.result-card.loser {
    background: linear-gradient(135deg, #ff4b2b 0%, #ff416c 100%);
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
}

.stat-item {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    border-left: 4px solid #667eea;
}

.stat-item .label {
    color: #6c757d;
    font-size: 0.9em;
    margin-bottom: 5px;
}

.stat-item .value {
    color: #495057;
    font-size: 1.4em;
    font-weight: bold;
}

/* Voting History (Flask-style) */
.voting-history {
    overflow-x: auto;
}

.voting-round {
    margin-bottom: 25px;
    background: #f8f9fa;
    border-radius: 8px;
    overflow: hidden;
}

.voting-round-header {
    background: #667eea;
    color: white;
    padding: 10px 20px;
    font-weight: bold;
}

.votes-list {
    padding: 15px 20px;
}

.vote-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #e9ecef;
}

.vote-item:last-child {
    border-bottom: none;
}

.voter {
    font-weight: 500;
    color: #495057;
}

.vote-arrow {
    color: #667eea;
    font-weight: bold;
    margin: 0 10px;
}

.target {
    font-weight: 500;
    color: #dc3545;
}
</style>