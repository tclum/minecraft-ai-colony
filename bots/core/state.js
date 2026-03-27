function observeBot(bot) {
    return {
        position: bot.entity?.position
            ? {
                x: bot.entity.position.x,
                y: bot.entity.position.y,
                z: bot.entity.position.z
            }
            : null,
        health: bot.health,
        food: bot.food,
        onGround: bot.entity?.onGround ?? false,
        inventory: bot.inventory.items().map(i => ({
            name: i.name,
            count: i.count
        }))
    }
}

module.exports = { observeBot }