const { GoalNear } = require('mineflayer-pathfinder').goals

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

function withTimeout(promise, ms, message = 'pathfinding_timeout') {
    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error(message)), ms)

        promise
            .then((value) => {
                clearTimeout(timer)
                resolve(value)
            })
            .catch((err) => {
                clearTimeout(timer)
                reject(err)
            })
    })
}

async function gatherWood(bot) {
    const block = bot.findBlock({
        matching: b => b && b.name && b.name.includes('log'),
        maxDistance: 32
    })

    if (!block) {
        return {
            success: false,
            reason: 'no_logs_found'
        }
    }

    console.log(`[${bot.username}] Found wood at ${block.position.x}, ${block.position.y}, ${block.position.z}`)

    try {
        await withTimeout(
            bot.pathfinder.goto(
                new GoalNear(block.position.x, block.position.y, block.position.z, 1)
            ),
            15000,
            'pathfinding_timeout'
        )
    } catch (err) {
        return {
            success: false,
            reason: 'pathfinding_failed',
            error: err.message
        }
    }

    const currentBlock = bot.blockAt(block.position)
    if (!currentBlock || !currentBlock.name || !currentBlock.name.includes('log')) {
        return {
            success: false,
            reason: 'log_no_longer_available'
        }
    }

    console.log(`[${bot.username}] Digging ${currentBlock.name}`)

    try {
        await bot.dig(currentBlock)
    } catch (digErr) {
        return {
            success: false,
            reason: 'dig_failed',
            error: digErr.message
        }
    }

    await sleep(700)

    return {
        success: true,
        reason: 'wood_gathered'
    }
}

module.exports = { gatherWood }