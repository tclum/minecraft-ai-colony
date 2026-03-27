require("dotenv").config();

const mineflayer = require("mineflayer");
const { pathfinder, Movements } = require("mineflayer-pathfinder");

const {
  loadMemory,
  saveMemory,
  updateMemoryFromObservation,
  startGoal,
  finishGoal,
  failGoal,
  startStep,
  finishStep,
} = require("../core/memory");

const { createLogger } = require("../core/logger");
const { observeBot } = require("../core/state");
const { getNextStep } = require("../planners/rule_planner");
const { explore } = require("../capabilities/movement");
const { gatherWood } = require("../capabilities/gather");
const { buildColumn } = require("../capabilities/build");
const {
  getNearestHostile,
  attackThreat,
  fleeThreat,
} = require("../capabilities/combat");
const BOT_NAME = process.env.TIM_BOT_NAME || "Tim";
const MC_HOST = process.env.MINECRAFT_HOST || "localhost";
const MC_PORT = Number(process.env.MINECRAFT_PORT || 25565);
const FLEE_HEALTH_THRESHOLD = 8; // flee below 4 hearts

const bot = mineflayer.createBot({
  host: MC_HOST,
  port: MC_PORT,
  username: BOT_NAME,
  version: "1.21.11", // add this
  keepAlive: true, // add this
  checkTimeoutInterval: 30000, // 30s before declaring timeout
});

bot.loadPlugin(pathfinder);

const logger = createLogger(BOT_NAME);
const memory = loadMemory(BOT_NAME, "generalist");

memory.currentGoal = null;
memory.currentStep = null;
memory.currentTask = null;
memory.goalStatus = "idle";
memory.stuckCount = memory.stuckCount || 0;
saveMemory(memory);

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function getLogCount(inventorySnapshot = {}) {
  if (
    !inventorySnapshot ||
    typeof inventorySnapshot !== "object" ||
    Array.isArray(inventorySnapshot)
  ) {
    return 0;
  }

  return Object.entries(inventorySnapshot)
    .filter(
      ([name, count]) =>
        typeof name === "string" &&
        name.endsWith("_log") &&
        typeof count === "number",
    )
    .reduce((sum, [, count]) => sum + count, 0);
}

function safeInventorySnapshot() {
  try {
    return bot.inventory.items().map((i) => ({
      name: i.name,
      count: i.count,
    }));
  } catch {
    return [];
  }
}

function refreshMemoryFromLiveBot() {
  updateMemoryFromObservation(memory, {
    position: bot.entity?.position
      ? {
          x: bot.entity.position.x,
          y: bot.entity.position.y,
          z: bot.entity.position.z,
        }
      : null,
    inventory: safeInventorySnapshot(),
  });
}

async function executeStep(step) {
  if (!step) {
    logger.warn("No step returned");
    return;
  }

  logger.info(`Executing step: ${JSON.stringify(step)}`);
  startStep(memory, step);
  saveMemory(memory);

  if (step.type === "explore") {
    const result = await explore(bot, step.radius || 16);

    if (!result?.success) {
      logger.warn(
        `Explore step failed: ${result?.reason || "unknown_reason"}${result?.error ? ` (${result.error})` : ""}`,
      );
      finishStep(memory);
      failGoal(memory);

      memory.currentGoal = null;
      startGoal(memory, { type: "scout_area", radius: 8 });
      logger.info("New goal: scout_area (reason: explore failed)");

      saveMemory(memory);
      return;
    }

    if (result.reason === "wood_spotted") {
      refreshMemoryFromLiveBot();
      finishStep(memory);

      memory.currentGoal = null;
      startGoal(memory, { type: "collect_wood" });
      logger.info(
        "New goal: collect_wood (reason: wood spotted during explore)",
      );

      saveMemory(memory);
      return;
    }

    refreshMemoryFromLiveBot();
    logger.info(
      `Post-explore inventory: ${JSON.stringify(memory.inventorySnapshot)}`,
    );
    finishStep(memory);
    saveMemory(memory);
    return;
  }

  if (step.type === "gatherWood") {
    const gatherStartedAt = Date.now();
    logger.info("Gather step starting");

    const result = await gatherWood(bot);

    logger.info(`Gather step finished in ${Date.now() - gatherStartedAt}ms`);

    if (!result?.success) {
      memory.stuckCount = (memory.stuckCount || 0) + 1;

      if (result.reason === "no_logs_found") {
        logger.warn("Gather step failed: no_logs_found");
      } else if (result.reason === "pathfinding_failed") {
        logger.warn(
          `Gather step failed: pathfinding_failed${result?.error ? ` (${result.error})` : ""}`,
        );
      } else if (result.reason === "log_no_longer_available") {
        logger.warn("Gather step failed: log_no_longer_available");
      } else if (result.reason === "dig_failed") {
        logger.warn(
          `Gather step failed: dig_failed${result?.error ? ` (${result.error})` : ""}`,
        );
      } else {
        logger.warn(`Gather step failed: ${result.reason || "unknown_reason"}`);
      }

      finishStep(memory);
      failGoal(memory);

      memory.currentGoal = null;

      if (memory.stuckCount >= 3) {
        memory.stuckCount = 0;
        startGoal(memory, { type: "scout_area", radius: 10 });
        logger.info("New goal: scout_area (reason: stuck in gather loop)");
      } else {
        startGoal(memory, { type: "scout_area", radius: 8 });
        logger.info("New goal: scout_area (reason: gather failed)");
      }

      saveMemory(memory);
      return;
    }

    memory.stuckCount = 0;
    refreshMemoryFromLiveBot();
    logger.info(
      `Post-gather inventory: ${JSON.stringify(memory.inventorySnapshot)}`,
    );
    logger.info(
      `Current total log count: ${getLogCount(memory.inventorySnapshot)}`,
    );
    finishStep(memory);
    finishGoal(memory);
    saveMemory(memory);
    return;
  }

  if (step.type === "buildColumn") {
    await buildColumn(bot, step.height || 3, step.block || "dirt");
    refreshMemoryFromLiveBot();
    logger.info(
      `Post-build inventory: ${JSON.stringify(memory.inventorySnapshot)}`,
    );
    finishStep(memory);
    finishGoal(memory);
    saveMemory(memory);
    return;
  }

  finishStep(memory);
  saveMemory(memory);
}

async function demoIdle(bot) {
  const action = Math.floor(Math.random() * 4);

  if (action === 0) {
    // look left or right
    const yaw = bot.entity.yaw + (Math.random() - 0.5) * 1.5;
    bot.look(yaw, 0, true);
  }

  if (action === 1) {
    // small hop
    bot.setControlState("jump", true);
    setTimeout(() => bot.setControlState("jump", false), 200);
  }

  if (action === 2) {
    // quick spin
    const yaw = bot.entity.yaw + Math.PI / 2;
    bot.look(yaw, 0, true);
  }

  if (action === 3) {
    // short step forward
    bot.setControlState("forward", true);
    setTimeout(() => bot.setControlState("forward", false), 400);
  }
}

async function workerLoop() {
  logger.info("Worker loop starting...");
  await sleep(700);

  memory.stuckCount = memory.stuckCount || 0;
  saveMemory(memory);

  while (true) {
    try {
      // PRIORITY 1: threat check — interrupts everything
      const threat = getNearestHostile(bot, 16);
      if (threat) {
        const health = bot.health ?? 20;

        if (health <= FLEE_HEALTH_THRESHOLD) {
          // Low health — flee first
          logger.info(`Low health (${health}/20) + threat detected — fleeing`);
          const prevGoal = memory.currentGoal;
          memory.currentGoal = null;
          startGoal(memory, { type: "flee" });
          saveMemory(memory);

          const result = await fleeThreat(bot, logger);
          logger.info(`Flee result: ${result.reason}`);

          memory.currentGoal = prevGoal;
          memory.goalStatus = prevGoal ? "active" : "idle";
          saveMemory(memory);
        } else {
          // Healthy — fight back
          logger.info(
            `Threat detected: ${threat.name} (health: ${health}/20) — attacking`,
          );
          const prevGoal = memory.currentGoal;
          memory.currentGoal = null;
          startGoal(memory, { type: "combat" });
          saveMemory(memory);

          const result = await attackThreat(bot, logger);
          logger.info(`Combat result: ${result.reason}`);

          memory.currentGoal = prevGoal;
          memory.goalStatus = prevGoal ? "active" : "idle";
          saveMemory(memory);
        }

        await sleep(500);
        continue;
      }
      const obs = observeBot(bot);
      updateMemoryFromObservation(memory, obs);
      saveMemory(memory);

      const totalLogs = getLogCount(memory.inventorySnapshot);
      logger.info(
        `Inventory snapshot: ${JSON.stringify(memory.inventorySnapshot)}`,
      );
      logger.info(`Current total log count: ${totalLogs}`);

      if (
        !memory.currentGoal ||
        memory.goalStatus === "failed" ||
        memory.goalStatus === "complete"
      ) {
        if (memory.goalStatus === "failed") {
          memory.currentGoal = null;
          startGoal(memory, { type: "scout_area", radius: 8 });
          logger.info("New goal: scout_area (reason: previous goal failed)");
        } else if (totalLogs < 5) {
          memory.currentGoal = null;
          startGoal(memory, { type: "collect_wood" });
          logger.info("New goal: collect_wood (reason: fewer than 5 logs)");
        } else {
          memory.currentGoal = null;
          startGoal(memory, {
            type: "build_column",
            height: 3,
            block: "dirt",
          });
          logger.info("New goal: build_column (reason: enough logs collected)");
        }
        saveMemory(memory);
      }

      if (memory.currentGoal && memory.goalStatus === "active") {
        const step = getNextStep(memory);
        logger.info(`Next step chosen: ${JSON.stringify(step)}`);
        await executeStep(step);
      }

      await demoIdle(bot);
      await sleep(500);
    } catch (err) {
      logger.error(`workerLoop error: ${err.message}`);
      failGoal(memory);
      saveMemory(memory);
      await sleep(500);
    }
  }
}

bot.once("spawn", () => {
  logger.info("Connected and spawned");
  const movements = new Movements(bot);
  movements.canDig = false;
  movements.allow1by1towers = false;
  movements.canOpenDoors = false;
  bot.pathfinder.setMovements(movements);

  // Make Tim unkillable via server command
  bot.chat("/effect give Tim resistance 999999 255 true");
  bot.chat("/effect give Tim fire_resistance 999999 255 true");

  workerLoop();
});

bot.on("death", () => {
  memory.deathCount = (memory.deathCount || 0) + 1;
  memory.currentGoal = null;
  memory.currentStep = null;
  memory.currentTask = null;
  memory.goalStatus = "idle";
  memory.stuckCount = 0;
  logger.warn(`Bot died. Total deaths: ${memory.deathCount}`);
  logger.info("Reset transient goal state after death");
  saveMemory(memory);
});

bot.on("health", () => {
  if (bot.health <= 4) {
    logger.warn(`Critical health: ${bot.health}/20 — will flee on next tick`);
  }
});

bot.on("error", (err) => {
  logger.error(`Bot error: ${err.message}`);
});

let reconnectCount = 0;
const MAX_RECONNECTS = 5;

bot.on("end", (reason) => {
  logger.warn(`Disconnected: ${reason}.`);
  saveMemory(memory);

  if (reconnectCount >= MAX_RECONNECTS) {
    logger.error("Max reconnects reached, exiting.");
    process.exit(1);
  }

  reconnectCount++;
  logger.warn(
    `Reconnecting in 5s... (attempt ${reconnectCount}/${MAX_RECONNECTS})`,
  );
  setTimeout(() => {
    require("child_process").spawn(process.execPath, process.argv.slice(1), {
      detached: false,
      stdio: "inherit",
    });
    process.exit();
  }, 5000);
});
