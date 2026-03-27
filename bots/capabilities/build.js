const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

async function buildColumn(bot, height = 3, blockName = 'dirt') {
    const item = bot.inventory.items().find(i => i.name === blockName)
    if (!item) {
        throw new Error(`Missing block ${blockName}`)
    }

    await bot.equip(item, 'hand')

    for (let i = 0; i < height; i++) {
        const reference = bot.blockAt(bot.entity.position.offset(0, -1, 0))
        if (!reference) {
            throw new Error('No reference block below')
        }

        await bot.placeBlock(reference, { x: 0, y: 1, z: 0 })
        await sleep(500)
    }
}

module.exports = { buildColumn }