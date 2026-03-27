const { GoalNear } = require('mineflayer-pathfinder').goals

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

async function explore(bot, radius = 16) {
    const pos = bot.entity.position
    const targetX = Math.floor(pos.x + (Math.random() * radius * 2 - radius))
    const targetY = Math.floor(pos.y)
    const targetZ = Math.floor(pos.z + (Math.random() * radius * 2 - radius))

    console.log(`[${bot.username}] Exploring toward ${targetX}, ${targetY}, ${targetZ}`)

    await bot.pathfinder.goto(new GoalNear(targetX, targetY, targetZ, 2))
    await sleep(500)
}

module.exports = { explore }