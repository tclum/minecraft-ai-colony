const { GoalNear } = require("mineflayer-pathfinder").goals;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function findNearbyLog(bot, maxDistance = 8) {
  return bot.findBlock({
    matching: (b) => b && b.name && b.name.includes("log"),
    maxDistance,
  });
}

function startBouncyMovement(bot) {
  return setInterval(() => {
    if (Math.random() < 0.35) {
      bot.setControlState("jump", true);
      setTimeout(() => bot.setControlState("jump", false), 200);
    }
  }, 600);
}

async function explore(bot, radius = 22) {
  const unreachableTargets = new Set();
  let bounce = null;

  for (let attempt = 0; attempt < 10; attempt++) {
    const pos = bot.entity.position;

    const nearbyLogBeforeMove = findNearbyLog(bot, 8);
    if (nearbyLogBeforeMove) {
      await bot.lookAt(nearbyLogBeforeMove.position.offset(0.5, 1, 0.5));
      console.log(
        `[${bot.username}] Wood spotted during explore at ${nearbyLogBeforeMove.position.x}, ${nearbyLogBeforeMove.position.y}, ${nearbyLogBeforeMove.position.z}`,
      );
      return { success: true, reason: "wood_spotted" };
    }

    let targetX, targetY, targetZ, targetKey;
    do {
      targetX = Math.floor(pos.x + (Math.random() * radius * 2 - radius));
      targetY = Math.floor(pos.y);
      targetZ = Math.floor(pos.z + (Math.random() * radius * 2 - radius));
      targetKey = `${targetX},${targetY},${targetZ}`;
    } while (unreachableTargets.has(targetKey));

    console.log(
      `[${bot.username}] Exploring toward ${targetX}, ${targetY}, ${targetZ} (attempt ${attempt + 1}/10)`,
    );

    try {
      bounce = startBouncyMovement(bot);
      await bot.pathfinder.goto(new GoalNear(targetX, targetY, targetZ, 2));
      clearInterval(bounce);
      bot.setControlState("jump", false);
      await sleep(500);

      const nearbyLogAfterMove = findNearbyLog(bot, 8);
      if (nearbyLogAfterMove) {
        await bot.lookAt(nearbyLogAfterMove.position.offset(0.5, 1, 0.5));
        console.log(
          `[${bot.username}] Wood spotted during explore at ${nearbyLogAfterMove.position.x}, ${nearbyLogAfterMove.position.y}, ${nearbyLogAfterMove.position.z}`,
        );
        return { success: true, reason: "wood_spotted" };
      }

      console.log(
        `[${bot.username}] Explore step succeeded at target ${targetX}, ${targetY}, ${targetZ}`,
      );
      console.log(`[${bot.username}] Completed explore successfully`);
      return { success: true, reason: "explore_complete" };
    } catch (e) {
      clearInterval(bounce);
      bot.setControlState("jump", false);
      const errMsg = e?.message || String(e);
      console.log(
        `[${bot.username}] Explore step failed: pathfinding_failed (${errMsg})`,
      );
      unreachableTargets.add(targetKey);
    }
  }

  return {
    success: false,
    reason: "pathfinding_failed",
    error: "No path to any explore target after 10 attempts",
  };
}

module.exports = { explore };
