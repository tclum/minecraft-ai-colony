const { GoalNear } = require("mineflayer-pathfinder").goals;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const recentlyFailed = new Set();

function withTimeout(promise, ms, message = "pathfinding_timeout") {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(message)), ms);

    promise
      .then((value) => {
        clearTimeout(timer);
        resolve(value);
      })
      .catch((err) => {
        clearTimeout(timer);
        reject(err);
      });
  });
}

async function gatherWood(bot) {
  // Find all nearby log blocks excluding recently failed locations
  const blocks = bot.findBlocks({
    matching: (b) => {
      if (!b || !b.position || !b.name) return false;
      if (!b.name.includes("log")) return false;
      const key = `${b.position.x},${b.position.y},${b.position.z}`;
      return !recentlyFailed.has(key);
    },
    maxDistance: 12,
    count: 20
  });

  if (!blocks.length) {
    recentlyFailed.clear();
    console.warn(
      `[${bot.username}] Gather failure: no_logs_found - no log blocks detected nearby.`
    );
    return {
      success: false,
      reason: "no_logs_found"
    };
  }

  console.log(
    `[${bot.username}] Navigating to tree at position ${blocks[0].x},${blocks[0].y},${blocks[0].z}`
  );

  // Choose the closest block
  let closestBlock = null;
  let closestDist = Infinity;
  const botPos = bot.entity.position;
  for (const pos of blocks) {
    const dist = botPos.distanceTo(pos);
    if (dist < closestDist) {
      closestDist = dist;
      closestBlock = pos;
    }
  }

  const key = `${closestBlock.x},${closestBlock.y},${closestBlock.z}`;

  try {
    await withTimeout(
      bot.pathfinder.goto(
        new GoalNear(closestBlock.x, closestBlock.y, closestBlock.z, 1)
      ),
      15000,
      "pathfinding_timeout"
    );
  } catch (err) {
    recentlyFailed.add(key);
    if (recentlyFailed.size > 10) recentlyFailed.clear();
    console.warn(
      `[${bot.username}] Gather failure: pathfinding_failed - ${err.message}`
    );
    return {
      success: false,
      reason: "pathfinding_failed",
      error: err.message
    };
  }

  const currentBlock = bot.blockAt(closestBlock);
  if (!currentBlock || !currentBlock.name || !currentBlock.name.includes("log")) {
    recentlyFailed.add(key);
    if (recentlyFailed.size > 10) recentlyFailed.clear();
    console.warn(
      `[${bot.username}] Gather failure: log_no_longer_available - block not a log anymore.`
    );
    return {
      success: false,
      reason: "log_no_longer_available"
    };
  }

  console.log(`[${bot.username}] Mining block at position ${closestBlock.x},${closestBlock.y},${closestBlock.z}`);

  try {
    await bot.dig(currentBlock);
  } catch (digErr) {
    recentlyFailed.add(key);
    if (recentlyFailed.size > 10) recentlyFailed.clear();
    console.warn(
      `[${bot.username}] Gather failure: dig_failed - ${digErr.message}`
    );
    return {
      success: false,
      reason: "dig_failed",
      error: digErr.message
    };
  }

  console.log(`[${bot.username}] Block broken at position ${closestBlock.x},${closestBlock.y},${closestBlock.z}`);

  recentlyFailed.delete(key);
  await sleep(700);

  // Log current inventory count for log items
  try {
    const logs = bot.inventory.items().filter(i => i.name.includes("log"));
    for (const log of logs) {
      console.log(`[${bot.username}] ${log.name}: ${log.count}`);
    }
  } catch {}

  console.log(`[${bot.username}] Gather step finished successfully`);

  return {
    success: true,
    reason: "wood_gathered"
  };
}

module.exports = { gatherWood };