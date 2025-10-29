const BASE = `${import.meta.env.BASE_URL}.training`

async function fetchJson(path) {
    const res = await fetch(path)
    if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`)
    return await res.json()
}

export async function getProgress() {
    try {
        return await fetchJson(`${BASE}/progress/progress.json`)
    } catch (e) {
        console.warn('无法加载 progress.json, 返回空列表', e)
        return { games_history: [] }
    }
}

export async function getRawLog(filename) {
    try {
        const res = await fetch(`${BASE}/game_logs/${filename}`)
        if (!res.ok) return `无法加载日志: ${res.status}`
        return await res.text()
    } catch (e) {
        return `加载日志出错: ${e.message}`
    }
}

export async function findReviewsForGame(filename) {
    // basic heuristic: reviews may be named similarly and live under /.training/reviews
    try {
        const res = await fetch(`${BASE}/reviews/`)
        // static servers don't list directories, so as fallback search by known names
    } catch (e) {
        // ignore
    }
    // attempt a few likely filenames
    const base = filename.replace(/\.txt$/i, '')
    const candidates = [`${base}_review.txt`, `${base}.json`, `${base}_review.json`]
    const found = []
    for (const c of candidates) {
        try {
            const url = `${BASE}/reviews/${c}`
            const r = await fetch(url)
            if (r.ok) found.push(url)
        } catch (e) { }
    }
    return found
}

export async function getParsedForGame(filename) {
    const base = filename.replace(/\.txt$/i, '')
    const candidates = [`${base}.json`, `${base}_parsed.json`, `${base}_data.json`]
    for (const c of candidates) {
        try {
            const url = `${BASE}/parsed_games/${c}`
            const r = await fetch(url)
            if (r.ok) return await r.json()
        } catch (e) { }
    }
    return null
}

export default { getProgress, getRawLog, findReviewsForGame, getParsedForGame }
