const fs = require('fs')
const path = require('path')

function getMemoryFilePath(botName) {
    return path.join(process.cwd(), 'memory', `${botName}.json`)
}

function ensureMemoryDir() {
    const memoryDir = path.join(process.cwd(), 'memory')
    if (!fs.existsSync(memoryDir)) {
        fs.mkdirSync(memoryDir, { recursive: true })
    }
}

function createMemory(botName, personality = 'generalist') {
    return {
        botName,
        displayName: botName,
        personality,
        role: 'generalist',
        status: 'idle',
        currentGoal: null,
        currentStep: null,
        currentTask: null,
        goalStatus: 'idle',
        lastGoalCompletedAt: null,
        lastCompletedGoal: null,
        lastCompletedStep: null,
        stepStartedAt: null,
        lastProgressAt: Date.now(),
        stuckCount: 0,
        inventorySnapshot: {},
        positionSnapshot: null,
        actionHistory: [],
        deathCount: 0,
        home: null
    }
}

function summarizeInventory(items = []) {
    const map = {}
    for (const item of items) {
        if (!item || !item.name) continue
        map[item.name] = (map[item.name] || 0) + (item.count || 0)
    }
    return map
}

function updateMemoryFromObservation(memory, obs = {}) {
    memory.inventorySnapshot = summarizeInventory(obs.inventory || [])
    memory.positionSnapshot = obs.position || null
    memory.status = 'active'
    memory.lastProgressAt = Date.now()
}

function startGoal(memory, goal) {
    memory.currentGoal = goal
    memory.currentTask = goal?.type || null
    memory.currentStep = null
    memory.goalStatus = 'active'
    memory.stepStartedAt = null
    memory.stuckCount = 0
    memory.lastProgressAt = Date.now()
}

function finishGoal(memory) {
    memory.lastCompletedGoal = memory.currentGoal
    memory.currentGoal = null
    memory.currentTask = null
    memory.currentStep = null
    memory.goalStatus = 'complete'
    memory.stepStartedAt = null
    memory.lastProgressAt = Date.now()
    memory.lastGoalCompletedAt = Date.now()
}

function failGoal(memory) {
    memory.goalStatus = 'failed'
    memory.currentStep = null
    memory.stepStartedAt = null
    memory.lastProgressAt = Date.now()
}

function startStep(memory, step) {
    memory.currentStep = step
    memory.stepStartedAt = Date.now()
    memory.lastProgressAt = Date.now()
}

function finishStep(memory) {
    memory.lastCompletedStep = memory.currentStep
    memory.currentStep = null
    memory.stepStartedAt = null
    memory.lastProgressAt = Date.now()
}

function saveMemory(memory) {
    ensureMemoryDir()
    const filePath = getMemoryFilePath(memory.botName)
    fs.writeFileSync(filePath, JSON.stringify(memory, null, 2), 'utf8')
}

function loadMemory(botName, personality = 'generalist') {
    ensureMemoryDir()
    const filePath = getMemoryFilePath(botName)

    if (!fs.existsSync(filePath)) {
        const freshMemory = createMemory(botName, personality)
        saveMemory(freshMemory)
        return freshMemory
    }

    try {
        const raw = fs.readFileSync(filePath, 'utf8')
        const parsed = JSON.parse(raw)

        return {
            ...createMemory(botName, personality),
            ...parsed
        }
    } catch (err) {
        const fallback = createMemory(botName, personality)
        saveMemory(fallback)
        return fallback
    }
}

module.exports = {
    createMemory,
    loadMemory,
    saveMemory,
    updateMemoryFromObservation,
    startGoal,
    finishGoal,
    failGoal,
    startStep,
    finishStep
}