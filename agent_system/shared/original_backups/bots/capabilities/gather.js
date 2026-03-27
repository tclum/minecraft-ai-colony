const { GoalNear } = require('mineflayer-pathfinder').goals

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

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
        await bot.pathfinder.goto(
            new GoalNear(block.position.x, block.position.y, block.position.z, 1)
        )
    } catch (err) {
        return {
            success: false,
            reason: 'pathfinding_failed',
            error: err.message
        }
    }

    console.log(`[${bot.username}] Digging ${block.name}`)
    await bot.dig(block)
    await sleep(700)

    return {
        success: true,
        reason: 'wood_gathered'
    }
}

module.exports = { gatherWood }