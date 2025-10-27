// Global state
let currentGameData = null;
let isPlaying = false;
let playInterval = null;
let playSpeed = 1000;

// Phase translations
const phaseTranslations = {
    'night': '夜晚',
    'morning': '早晨',
    'day': '白天',
    'voting': '投票',
    'start': '开始'
};

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
};

// Role translations
const roleTranslations = {
    'werewolf': '狼人',
    'villager': '村民',
    'seer': '预言家',
    'witch': '女巫',
    'hunter': '猎人',
    'guardian': '守卫',
    'unknown': '未知'
};

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    loadAvailableLogs();
    setupEventListeners();
});

// Load available log files
async function loadAvailableLogs() {
    try {
        const response = await fetch('/api/logs');
        const logs = await response.json();

        const logList = document.getElementById('log-list');

        if (logs.length === 0) {
            logList.innerHTML = '<p class="loading">没有找到游戏日志文件</p>';
            return;
        }

        logList.innerHTML = '';

        logs.forEach(log => {
            const logItem = document.createElement('div');
            logItem.className = 'log-item';

            const date = new Date(log.modified * 1000);
            const dateStr = date.toLocaleString('zh-CN');

            logItem.innerHTML = `
                <h3>${log.filename}</h3>
                <div class="log-meta">
                    <div>日期: ${dateStr}</div>
                    <div>大小: ${(log.size / 1024).toFixed(2)} KB</div>
                </div>
            `;

            logItem.addEventListener('click', () => loadLog(log.filename));
            logList.appendChild(logItem);
        });
    } catch (error) {
        console.error('Failed to load logs:', error);
        document.getElementById('log-list').innerHTML =
            '<p class="loading">加载日志列表失败</p>';
    }
}

// Load a specific log file
async function loadLog(filename) {
    try {
        const response = await fetch(`/api/load/${filename}`);
        const data = await response.json();

        if (data.error) {
            alert('加载失败: ' + data.error);
            return;
        }

        currentGameData = data;

        // Hide log selector and show game container
        document.getElementById('log-selector').classList.add('hidden');
        document.getElementById('game-container').classList.remove('hidden');

        // Display game info
        displayGameInfo(data.game_info);

        // Display players
        displayPlayers(data.players);

        // Load initial state
        await updateState();

    } catch (error) {
        console.error('Failed to load log:', error);
        alert('加载游戏日志失败');
    }
}

// Display game information
function displayGameInfo(gameInfo) {
    document.getElementById('game-type').textContent = gameInfo.game_type || '-';
    document.getElementById('rounds-played').textContent = gameInfo.rounds_played || '-';
    document.getElementById('winner').textContent = gameInfo.winner || '-';
}

// Display players in a grid
function displayPlayers(players) {
    const container = document.getElementById('players-container');
    container.innerHTML = '';

    Object.values(players).forEach(player => {
        const card = document.createElement('div');
        card.className = 'player-card';
        card.id = `player-${player.name}`;

        card.innerHTML = `
            <div class="player-name">${player.name}</div>
            <div class="player-role">${roleTranslations[player.role] || player.role}</div>
            <div class="player-status">${player.status === 'alive' ? '存活' : '死亡'}</div>
        `;

        container.appendChild(card);
    });
}

// Update player cards based on current state
function updatePlayerCards(playerStates) {
    Object.entries(playerStates).forEach(([name, state]) => {
        const card = document.getElementById(`player-${name}`);
        if (!card) return;

        // Update class
        card.className = 'player-card';
        if (state.status === 'dead') {
            card.classList.add('dead');
        } else {
            card.classList.add('alive');
        }

        if (state.revealed && state.role === 'werewolf') {
            card.classList.add('werewolf');
        }

        // Update role display
        const roleElement = card.querySelector('.player-role');
        roleElement.textContent = roleTranslations[state.role] || state.role;

        // Update status
        const statusElement = card.querySelector('.player-status');
        statusElement.textContent = state.status === 'alive' ? '存活' : '死亡';
    });
}

// Update game state
async function updateState() {
    try {
        const response = await fetch('/api/state');
        const state = await response.json();

        if (state.error) {
            console.error('State error:', state.error);
            return;
        }

        // Update progress
        const progress = state.total_events > 0
            ? (state.event_index / state.total_events) * 100
            : 0;
        document.getElementById('progress-fill').style.width = progress + '%';
        document.getElementById('progress-handle').style.left = progress + '%';
        document.getElementById('progress-text').textContent =
            `${state.event_index} / ${state.total_events}`;

        // Update player cards
        updatePlayerCards(state.player_states);

        // Display current event
        displayEvent(state.current_event);

        // Update phase indicator
        if (state.current_event) {
            document.getElementById('current-round').textContent =
                `回合 ${state.current_event.round_num}`;
            document.getElementById('current-phase').textContent =
                `阶段: ${phaseTranslations[state.current_event.phase] || state.current_event.phase}`;
        }

        // Stop playing if finished
        if (state.is_finished && isPlaying) {
            stopPlaying();
        }

    } catch (error) {
        console.error('Failed to update state:', error);
    }
}

// Display event details
function displayEvent(event) {
    const content = document.getElementById('event-content');

    if (!event) {
        content.innerHTML = '<p>游戏结束</p>';
        return;
    }

    let html = `<div class="event-type">${eventTypeTranslations[event.event_type] || event.event_type}</div>`;

    switch (event.event_type) {
        case 'phase_start':
            html += `<p>进入 <strong>${phaseTranslations[event.data.phase]}</strong> 阶段</p>`;
            break;

        case 'guardian_action':
            if (event.data.action === 'no_protection') {
                html += `<div class="event-data">`;
                html += `<p>🛡️ 本局没有守卫，或守卫未行动</p>`;
                html += `</div>`;
            } else if (event.data.guardian && event.data.protected) {
                html += `<div class="event-data">`;
                html += `<p>🛡️ 守卫 <strong>${event.data.guardian}</strong> 保护了 <strong>${event.data.protected}</strong></p>`;
                html += `</div>`;
            } else {
                html += `<div class="event-data">`;
                html += `<p>🛡️ 守卫正在行动...</p>`;
                html += `</div>`;
            }
            break;

        case 'werewolf_target':
            html += '<div class="event-data">';
            html += '<p><strong>狼人选择目标:</strong></p>';
            for (const [werewolf, target] of Object.entries(event.data.targets)) {
                html += `<p>🐺 ${werewolf} → ${target}</p>`;
            }
            html += '</div>';
            break;

        case 'seer_check':
            html += `<div class="event-data">`;
            html += `<p>🔮 预言家 <strong>${event.data.seer}</strong> 查验 <strong>${event.data.target}</strong></p>`;
            html += `</div>`;
            break;

        case 'seer_result':
            const resultText = event.data.result === 'werewolf' ? '是狼人' : '是好人';
            html += `<div class="event-data">`;
            html += `<p>🔮 预言家得知: <strong>${event.data.target}</strong> ${resultText}</p>`;
            html += `</div>`;
            break;

        case 'witch_save':
            const saveText = event.data.saved ? '救了' : '没有救';
            html += `<div class="event-data">`;
            html += `<p>💊 女巫 ${saveText} <strong>${event.data.target}</strong></p>`;
            html += `</div>`;
            break;

        case 'witch_poison':
            html += `<div class="event-data">`;
            html += `<p>💊 女巫 ${event.data.used ? '使用了' : '没有使用'} 毒药</p>`;
            html += `</div>`;
            break;

        case 'death_announcement':
            html += `<div class="death-announcement">`;
            html += `<p>☠️ <strong>${event.data.player}</strong> 在夜晚死亡</p>`;
            html += `<p>原因: ${event.data.reason}</p>`;
            html += `</div>`;
            break;

        case 'last_words':
            html += `<div class="last-words">`;
            html += `<p><strong>${event.data.player}</strong> 的遗言:</p>`;
            html += `<p>"${event.data.statement}"</p>`;
            html += `</div>`;
            break;

        case 'alive_players':
            html += `<div class="event-data">`;
            html += `<p><strong>存活玩家:</strong> ${event.data.players.join(', ')}</p>`;
            html += `</div>`;
            break;

        case 'discussion':
            html += `<div class="discussion-bubble">`;
            html += `<div class="speaker">💬 ${event.data.speaker}:</div>`;
            html += `<div class="statement">${event.data.statement}</div>`;
            html += `</div>`;
            break;

        case 'vote':
            html += `<div class="event-data">`;
            html += `<p>🗳️ <strong>${event.data.voter}</strong> 投票给 <strong>${event.data.target}</strong></p>`;
            html += `</div>`;
            break;

        case 'vote_summary':
            html += `<div class="event-data">`;
            html += `<p><strong>投票结果:</strong></p>`;
            for (const [target, voters] of Object.entries(event.data.votes)) {
                html += `<div class="vote-info">${target}: ${voters.length}票 (${voters.join(', ')})</div>`;
            }
            html += `</div>`;
            break;

        case 'elimination':
            html += `<div class="death-announcement">`;
            html += `<p>⚖️ <strong>${event.data.player}</strong> 被投票淘汰</p>`;
            html += `<p>角色: ${roleTranslations[event.data.role] || event.data.role}</p>`;
            html += `</div>`;
            break;

        case 'hunter_skill':
            html += `<div class="hunter-skill">`;
            html += `<p>🎯 <strong>猎人技能触发!</strong></p>`;
            html += `<p>🔫 猎人 <strong>${event.data.hunter}</strong> 开枪射杀了 <strong>${event.data.target}</strong></p>`;
            html += `<p>💀 ${event.data.target} 的角色是: <strong>${roleTranslations[event.data.target_role] || event.data.target_role}</strong></p>`;
            html += `</div>`;
            break;

        default:
            html += `<div class="event-data"><pre>${JSON.stringify(event.data, null, 2)}</pre></div>`;
    }

    content.innerHTML = html;
    content.classList.add('fade-in');

    // Remove animation class after animation completes
    setTimeout(() => content.classList.remove('fade-in'), 500);
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('btn-reset').addEventListener('click', async () => {
        stopPlaying();
        await fetch('/api/reset');
        await updateState();
    });

    document.getElementById('btn-prev').addEventListener('click', async () => {
        stopPlaying();
        await fetch('/api/prev');
        await updateState();
    });

    document.getElementById('btn-play').addEventListener('click', () => {
        if (isPlaying) {
            stopPlaying();
        } else {
            startPlaying();
        }
    });

    document.getElementById('btn-next').addEventListener('click', async () => {
        stopPlaying();
        await fetch('/api/next');
        await updateState();
    });

    document.getElementById('btn-back').addEventListener('click', () => {
        stopPlaying();
        document.getElementById('game-container').classList.add('hidden');
        document.getElementById('log-selector').classList.remove('hidden');
    });

    document.getElementById('btn-overview').addEventListener('click', showGameOverview);

    document.getElementById('speed-select').addEventListener('change', (e) => {
        playSpeed = parseInt(e.target.value);
        if (isPlaying) {
            stopPlaying();
            startPlaying();
        }
    });

    // Modal close functionality
    const modal = document.getElementById('overview-modal');
    const closeBtn = modal.querySelector('.close');

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            switchTab(tabName);
        });
    });

    // Progress bar drag and click
    setupProgressBarControls();

    // Keyboard controls
    setupKeyboardControls();
}

// Setup progress bar drag and click
function setupProgressBarControls() {
    const progressBar = document.getElementById('progress-bar');
    const progressFill = document.getElementById('progress-fill');
    const progressHandle = document.getElementById('progress-handle');
    let isDragging = false;

    // Click to jump
    progressBar.addEventListener('click', async (e) => {
        if (isDragging) return;

        const rect = progressBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;

        // Get current state to know total events
        const stateResponse = await fetch('/api/state');
        const state = await stateResponse.json();

        if (state.total_events > 0) {
            const targetIndex = Math.round(percentage * state.total_events);
            stopPlaying();
            await fetch(`/api/jump/${targetIndex}`);
            await updateState();
        }
    });

    // Drag handle
    progressHandle.addEventListener('mousedown', (e) => {
        isDragging = true;
        progressBar.classList.add('dragging');
        stopPlaying();
        e.preventDefault();
    });

    document.addEventListener('mousemove', async (e) => {
        if (!isDragging) return;

        const rect = progressBar.getBoundingClientRect();
        let clickX = e.clientX - rect.left;

        // Clamp to bar width
        clickX = Math.max(0, Math.min(clickX, rect.width));
        const percentage = clickX / rect.width;

        // Update visual immediately
        progressFill.style.width = (percentage * 100) + '%';
        progressHandle.style.left = (percentage * 100) + '%';
    });

    document.addEventListener('mouseup', async (e) => {
        if (!isDragging) return;

        isDragging = false;
        progressBar.classList.remove('dragging');

        const rect = progressBar.getBoundingClientRect();
        let clickX = e.clientX - rect.left;
        clickX = Math.max(0, Math.min(clickX, rect.width));
        const percentage = clickX / rect.width;

        // Get current state to know total events
        const stateResponse = await fetch('/api/state');
        const state = await stateResponse.json();

        if (state.total_events > 0) {
            const targetIndex = Math.round(percentage * state.total_events);
            await fetch(`/api/jump/${targetIndex}`);
            await updateState();
        }
    });
}

// Setup keyboard controls
function setupKeyboardControls() {
    document.addEventListener('keydown', async (e) => {
        // Only handle arrow keys when game is loaded
        const gameContainer = document.getElementById('game-container');
        if (gameContainer.classList.contains('hidden')) return;

        // Ignore if user is typing in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        switch (e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                stopPlaying();
                await fetch('/api/prev');
                await updateState();
                break;

            case 'ArrowRight':
                e.preventDefault();
                stopPlaying();
                await fetch('/api/next');
                await updateState();
                break;

            case ' ':
                e.preventDefault();
                if (isPlaying) {
                    stopPlaying();
                } else {
                    startPlaying();
                }
                break;
        }
    });
}

// Start auto-playing
function startPlaying() {
    isPlaying = true;
    document.getElementById('btn-play').textContent = '⏸ 暂停';

    playInterval = setInterval(async () => {
        const response = await fetch('/api/next');
        const state = await response.json();

        await updateState();

        if (state.is_finished) {
            stopPlaying();
        }
    }, playSpeed);
}

// Stop playing
function stopPlaying() {
    isPlaying = false;
    document.getElementById('btn-play').textContent = '▶ 播放';

    if (playInterval) {
        clearInterval(playInterval);
        playInterval = null;
    }
}

// Show game overview modal
async function showGameOverview() {
    try {
        const response = await fetch('/api/overview');
        const overview = await response.json();

        if (overview.error) {
            alert('获取游戏概览失败: ' + overview.error);
            return;
        }

        // Populate overview data
        populateGameSummary(overview);
        populatePlayersOverview(overview);
        populateDeathTimeline(overview);
        populateVotingHistory(overview);
        populateSpecialActions(overview);

        // Show modal
        document.getElementById('overview-modal').style.display = 'block';

    } catch (error) {
        console.error('Failed to load game overview:', error);
        alert('加载游戏概览失败');
    }
}

// Switch tabs in overview modal
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });

    // Show selected tab content
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // Set active tab button
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
}

// Populate game summary tab
function populateGameSummary(overview) {
    const resultContent = document.getElementById('game-result-content');
    const statsContent = document.getElementById('game-stats-content');

    // Game result
    const result = overview.final_result;
    const winnerClass = result.winner === 'WEREWOLVES' ? 'loser' : 'winner'; // From villager perspective

    resultContent.innerHTML = `
        <div class="result-card ${winnerClass}">
            <div class="title">游戏结果</div>
            <div class="value">${result.winner === 'WEREWOLVES' ? '🐺 狼人胜利' : '👥 村民胜利'}</div>
        </div>
        <div class="result-card">
            <div class="title">游戏回合数</div>
            <div class="value">${result.rounds_played}</div>
        </div>
        <div class="result-card">
            <div class="title">剩余狼人</div>
            <div class="value">${result.werewolves_remaining}</div>
        </div>
        <div class="result-card">
            <div class="title">剩余村民</div>
            <div class="value">${result.villagers_remaining}</div>
        </div>
    `;

    // Game statistics
    const totalPlayers = Object.keys(overview.players).length;
    const totalDeaths = overview.death_timeline.length;
    const totalVotes = overview.voting_history.length;
    const totalSpecialActions = overview.special_actions.length;

    statsContent.innerHTML = `
        <div class="stat-item">
            <div class="label">总玩家数</div>
            <div class="value">${totalPlayers}</div>
        </div>
        <div class="stat-item">
            <div class="label">死亡人数</div>
            <div class="value">${totalDeaths}</div>
        </div>
        <div class="stat-item">
            <div class="label">投票次数</div>
            <div class="value">${totalVotes}</div>
        </div>
        <div class="stat-item">
            <div class="label">特殊行动</div>
            <div class="value">${totalSpecialActions}</div>
        </div>
        <div class="stat-item">
            <div class="label">狼人初始数量</div>
            <div class="value">${Object.values(overview.players).filter(p => p.role === 'werewolf').length}</div>
        </div>
        <div class="stat-item">
            <div class="label">特殊角色数量</div>
            <div class="value">${Object.values(overview.players).filter(p => !['werewolf', 'villager'].includes(p.role)).length}</div>
        </div>
    `;
}

// Populate players overview tab
function populatePlayersOverview(overview) {
    const content = document.getElementById('players-overview-content');

    let html = '';
    Object.values(overview.players).forEach(player => {
        const isWerewolf = player.role === 'werewolf';
        const isDead = player.final_status === 'dead';
        const cardClass = `player-overview-card ${isWerewolf ? 'werewolf' : ''} ${isDead ? 'dead' : ''}`;

        const statusText = isDead ? `死亡 (第${player.death_round}回合, ${player.death_reason})` : '存活';

        let actionsText = '';
        if (player.actions_taken.length > 0) {
            actionsText = `行动: ${player.actions_taken.map(a => `${eventTypeTranslations[a.action] || a.action}(${a.target})`).join(', ')}`;
        }

        let votesText = '';
        if (player.votes_cast.length > 0) {
            votesText = `投票: ${player.votes_cast.map(v => `R${v.round}→${v.target}`).join(', ')}`;
        }

        html += `
            <div class="${cardClass}">
                <div class="player-name">${player.name}</div>
                <div class="player-role">${roleTranslations[player.role] || player.role}</div>
                <div class="player-status">${statusText}</div>
                <div class="player-actions">
                    ${actionsText}<br>
                    ${votesText}
                </div>
            </div>
        `;
    });

    content.innerHTML = html;
}

// Populate death timeline tab
function populateDeathTimeline(overview) {
    const content = document.getElementById('death-timeline-content');

    if (overview.death_timeline.length === 0) {
        content.innerHTML = '<p class="no-data">没有玩家死亡记录</p>';
        return;
    }

    let html = '';
    overview.death_timeline.forEach(death => {
        html += `
            <div class="timeline-item">
                <div class="round-badge">第${death.round}回合</div>
                <div class="death-info">${death.player} 死亡</div>
                <div class="death-reason">阶段: ${phaseTranslations[death.phase]} | 原因: ${death.reason}</div>
            </div>
        `;
    });

    content.innerHTML = html;
}

// Populate voting history tab
function populateVotingHistory(overview) {
    const content = document.getElementById('voting-history-content');

    if (overview.voting_history.length === 0) {
        content.innerHTML = '<p class="no-data">没有投票记录</p>';
        return;
    }

    // Group votes by round
    const votesByRound = {};
    overview.voting_history.forEach(vote => {
        if (!votesByRound[vote.round]) {
            votesByRound[vote.round] = [];
        }
        votesByRound[vote.round].push(vote);
    });

    let html = '';
    Object.keys(votesByRound).sort((a, b) => parseInt(a) - parseInt(b)).forEach(round => {
        const votes = votesByRound[round];
        html += `
            <div class="voting-round">
                <div class="voting-round-header">第${round}回合投票</div>
                <div class="votes-list">
        `;

        votes.forEach(vote => {
            html += `
                <div class="vote-item">
                    <span class="voter">${vote.voter}</span>
                    <span class="vote-arrow">→</span>
                    <span class="target">${vote.target}</span>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;
    });

    content.innerHTML = html;
}

// Populate special actions tab
function populateSpecialActions(overview) {
    const content = document.getElementById('special-actions-content');

    if (overview.special_actions.length === 0) {
        content.innerHTML = '<p class="no-data">没有特殊行动记录</p>';
        return;
    }

    let html = '';
    overview.special_actions.forEach(action => {
        const actionClass = action.type.includes('werewolf') ? 'werewolf-action' :
            action.type.includes('seer') ? 'seer-action' :
                action.type.includes('witch') ? 'witch-action' :
                    action.type.includes('hunter') ? 'hunter-action' : '';

        const actionName = eventTypeTranslations[action.type] || action.type;
        const targetText = action.target ? ` → ${action.target}` : '';
        const resultText = action.result ? ` (${action.result})` : '';

        html += `
            <div class="action-item ${actionClass}">
                <div class="action-header">
                    <span class="action-type">${actionName}</span>
                    <span class="action-round">第${action.round}回合 ${phaseTranslations[action.phase]}</span>
                </div>
                <div class="action-details">${action.actor}${targetText}</div>
                <div class="action-result">${resultText}</div>
            </div>
        `;
    });

    content.innerHTML = html;
}
