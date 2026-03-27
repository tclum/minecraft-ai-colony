require('dotenv').config()

const mineflayer = require('mineflayer')
const { pathfinder, Movements } = require('mineflayer-pathfinder')

const {
    loadMemory,
    saveMemory,
    updateMemoryFromObservation,
    startGoal,
    finishGoal,
    failGoal,
    startStep,
    finishStep
} = require('../core/memory')

const { createLogger } = require('../core/logger')
const { observeBot } = require('../core/state')
const { getNextStep } = require('../planners/rule_planner')
const { explore } = require('../capabilities/movement')
const { gatherWood } = require('../capabilities/gather')
const { buildColumn } = require('../capabilities/build')

const BOT_NAME = process.env.TIM_BOT_NAME || 'Tim'
const MC_HOST = process.env.MINECRAFT_HOST || 'localhost'
const MC_PORT = Number(process.env.MINECRAFT_PORT || 25565)

const bot = mineflayer.createBot({
    host: MC_HOST,
    port: MC_PORT,
    username: BOT_NAME
})

bot.loadPlugin(pathfinder)

const logger = createLogger(BOT_NAME)
const memory = loadMemory(BOT_NAME, 'generalist')

memory.currentGoal = null
memory.currentStep = null
memory.currentTask = null
memory.goalStatus = 'idle'
saveMemory(memory)

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

function getLogCount(inventorySnapshot = {}) {
    return Object.entries(inventorySnapshot)
        .filter(([name]) => name.endsWith('_log'))
        .reduce((sum, [, count]) => sum + count, 0)
}

function safeInventorySnapshot() {
    try {
        return bot.inventory.items().map(i => ({
            name: i.name,
            count: i.count
        }))
    } catch {
        return []
    }
}

function refreshMemoryFromLiveBot() {
    updateMemoryFromObservation(memory, {
        position: bot.entity?.position
            ? {
                x: bot.entity.position.x,
                y: bot.entity.position.y,
                z: bot.entity.position.z
            }
            : null,
        inventory: safeInventorySnapshot()
    })
}

async function executeStep(step) {
    if (!step) {
        logger.warn('No step returned')
        return
    }

    logger.info(`Executing step: ${JSON.stringify(step)}`)
    startStep(memory, step)
    saveMemory(memory)

    if (step.type === 'explore') {
        await explore(bot, step.radius || 16)
        refreshMemoryFromLiveBot()
        logger.info(`Post-explore inventory: ${JSON.stringify(memory.inventorySnapshot)}`)
        finishStep(memory)
        saveMemory(memory)
        return
    }

    if (step.type === 'gatherWood') {
        const result = await gatherWood(bot)

        if (!result?.success && result?.reason === 'no_logs_found') {
            logger.warn('No logs found nearby. Falling back to exploration.')
            finishStep(memory)
            failGoal(memory)
            saveMemory(memory)
            return
        }

        refreshMemoryFromLiveBot()
        logger.info(`Post-gather inventory: ${JSON.stringify(memory.inventorySnapshot)}`)
        logger.info(`Current total log count: ${getLogCount(memory.inventorySnapshot)}`)
        finishStep(memory)
        finishGoal(memory)
        saveMemory(memory)
        return
    }

    if (step.type === 'buildColumn') {
        await buildColumn(bot, step.height || 3, step.block || 'dirt')
        refreshMemoryFromLiveBot()
        logger.info(`Post-build inventory: ${JSON.stringify(memory.inventorySnapshot)}`)
        finishStep(memory)
        finishGoal(memory)
        saveMemory(memory)
        return
    }

    finishStep(memory)
    saveMemory(memory)
}

async function workerLoop() {
    logger.info('Worker loop starting...')
    await sleep(1500)

    while (true) {
        try {
            const obs = observeBot(bot)
            updateMemoryFromObservation(memory, obs)
            saveMemory(memory)

            const totalLogs = getLogCount(memory.inventorySnapshot)
            logger.info(`Inventory snapshot: ${JSON.stringify(memory.inventorySnapshot)}`)
            logger.info(`Current total log count: ${totalLogs}`)

            if (!memory.currentGoal || memory.goalStatus === 'failed' || memory.goalStatus === 'complete') {
                if (memory.goalStatus === 'failed') {
                    memory.currentGoal = null
                    startGoal(memory, { type: 'scout_area', radius: 12 })
                    logger.info('New goal: scout_area (reason: previous goal failed)')
                } else if (totalLogs < 3) {
                    memory.currentGoal = null
                    startGoal(memory, { type: 'collect_wood' })
                    logger.info('New goal: collect_wood (reason: fewer than 3 logs)')
                } else {
                    memory.currentGoal = null
                    startGoal(memory, { type: 'scout_area', radius: 12 })
                    logger.info('New goal: scout_area (reason: enough logs collected)')
                }
                saveMemory(memory)
            }

            if (memory.currentGoal && memory.goalStatus === 'active') {
                const step = getNextStep(memory)
                logger.info(`Next step chosen: ${JSON.stringify(step)}`)
                await executeStep(step)
            }

            await sleep(5000)
        } catch (err) {
            logger.error(`workerLoop error: ${err.message}`)
            failGoal(memory)
            saveMemory(memory)
            await sleep(3000)
        }
    }
}

bot.once('spawn', () => {
    logger.info('Connected and spawned')
    const movements = new Movements(bot)
    bot.pathfinder.setMovements(movements)
    workerLoop()
})

bot.on('death', () => {
    memory.deathCount = (memory.deathCount || 0) + 1
    logger.warn(`Bot died. Total deaths: ${memory.deathCount}`)
    saveMemory(memory)
})

bot.on('error', (err) => {
    logger.error(`Bot error: ${err.message}`)
})

bot.on('end', () => {
    logger.warn('Disconnected')
    saveMemory(memory)
})