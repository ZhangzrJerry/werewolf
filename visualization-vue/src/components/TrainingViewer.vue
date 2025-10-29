<template>
    <div class="training-viewer">
        <section class="list">
            <h2>游戏列表</h2>
            <div v-if="loading">加载中...</div>
            <div v-else>
                <ul>
                    <li v-for="game in games" :key="game.log_file">
                        <button @click="selectGame(game)">
                            游戏 #{{ game.game_num }} — 回合: {{ game.rounds }} — 胜者: {{ game.winner }} — {{
                            formatTime(game.timestamp) }}
                        </button>
                    </li>
                </ul>
            </div>
        </section>

        <section class="viewer" v-if="selected">
            <h2>日志: 游戏 #{{ selected.game_num }}</h2>
            <div class="meta">
                <p><strong>文件:</strong> {{ getFilename(selected.log_file) }}</p>
                <p><strong>胜者:</strong> {{ selected.winner }}</p>
                <p><strong>回合:</strong> {{ selected.rounds }}</p>
            </div>

            <div class="tabs">
                <button :class="{ active: tab === 'raw' }" @click="tab = 'raw'">原始日志</button>
                <button :class="{ active: tab === 'reviews' }" @click="tab = 'reviews'">复盘</button>
                <button :class="{ active: tab === 'parsed' }" @click="tab = 'parsed'">解析(JSON)</button>
            </div>

            <div class="content">
                <pre v-if="tab === 'raw'">{{ raw || '正在加载...' }}</pre>

                <div v-if="tab === 'reviews'">
                    <div v-if="reviews.length === 0">未找到复盘文件</div>
                    <ul>
                        <li v-for="r in reviews" :key="r"><a :href="r" target="_blank">{{ r }}</a></li>
                    </ul>
                </div>

                <pre v-if="tab === 'parsed'">{{ parsed ? JSON.stringify(parsed, null, 2) : '未找到解析文件' }}</pre>
            </div>
        </section>
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { getProgress, getRawLog, findReviewsForGame, getParsedForGame } from '../services/trainingService'

export default {
    name: 'TrainingViewer',
    setup() {
        const loading = ref(true)
        const games = ref([])
        const selected = ref(null)
        const raw = ref('')
        const reviews = ref([])
        const parsed = ref(null)
        const tab = ref('raw')

        async function load() {
            loading.value = true
            const p = await getProgress()
            games.value = p.games_history || []
            loading.value = false
        }

        async function selectGame(game) {
            selected.value = game
            raw.value = ''
            parsed.value = null
            reviews.value = []
            tab.value = 'raw'

            const filename = getFilename(game.log_file)
            raw.value = await getRawLog(filename)
            reviews.value = await findReviewsForGame(filename)
            parsed.value = await getParsedForGame(filename)
        }

        function getFilename(p) {
            // some entries use backslashes
            return p.replace(/^.*game_logs[\\\/]/, '')
        }

        function formatTime(ts) {
            try { return new Date(ts).toLocaleString() } catch { return ts }
        }

        onMounted(load)
        return { loading, games, selected, selectGame, raw, reviews, parsed, tab, getFilename, formatTime }
    }
}
</script>

<style scoped>
.training-viewer {
    display: flex;
    gap: 20px
}

.list {
    width: 320px
}

.list ul {
    list-style: none;
    padding: 0
}

.list button {
    width: 100%;
    text-align: left;
    padding: 8px;
    margin: 4px 0;
    border: 1px solid #ddd;
    background: #fff
}

.viewer {
    flex: 1
}

.meta p {
    margin: 4px 0
}

.tabs button {
    margin-right: 8px
}

.tabs .active {
    font-weight: bold
}

.content pre {
    background: #f7f7f7;
    padding: 12px;
    max-height: 60vh;
    overflow: auto
}
</style>
