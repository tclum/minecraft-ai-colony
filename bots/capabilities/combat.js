const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const HOSTILE_MOBS = new Set([
  "zombie",
  "skeleton",
  "spider",
  "cave_spider",
  "slime",
  "witch",
  "pillager",
  "vindicator",
  "phantom",
  "drowned",
  "husk",
  "stray",
  "enderman",
  "silverfish",
]);

const WEAPON_PRIORITY = [
  "netherite_sword",
  "diamond_sword",
  "iron_sword",
  "stone_sword",
  "wooden_sword",
  "netherite_axe",
  "diamond_axe",
  "iron_axe",
  "stone_axe",
  "wooden_axe",
];

const ARMOR_SLOTS = {
  head: [
    "netherite_helmet",
    "diamond_helmet",
    "iron_helmet",
    "chainmail_helmet",
    "golden_helmet",
    "leather_helmet",
  ],
  chest: [
    "netherite_chestplate",
    "diamond_chestplate",
    "iron_chestplate",
    "chainmail_chestplate",
    "golden_chestplate",
    "leather_chestplate",
  ],
  legs: [
    "netherite_leggings",
    "diamond_leggings",
    "iron_leggings",
    "chainmail_leggings",
    "golden_leggings",
    "leather_leggings",
  ],
  feet: [
    "netherite_boots",
    "diamond_boots",
    "iron_boots",
    "chainmail_boots",
    "golden_boots",
    "leather_boots",
  ],
};

function getNearestHostile(bot, maxDistance = 16) {
  return (
    Object.values(bot.entities).find((entity) => {
      if (!entity || !entity.name) return false;
      if (!HOSTILE_MOBS.has(entity.name)) return false;
      const dist = bot.entity.position.distanceTo(entity.position);
      return dist <= maxDistance;
    }) || null
  );
}

async function equipBestWeapon(bot) {
  const items = bot.inventory.items();
  for (const weaponName of WEAPON_PRIORITY) {
    const weapon = items.find((i) => i.name === weaponName);
    if (weapon) {
      try {
        await bot.equip(weapon, "hand");
        return weaponName;
      } catch {}
    }
  }
  return null;
}

async function equipArmor(bot) {
  for (const [slot, priority] of Object.entries(ARMOR_SLOTS)) {
    const items = bot.inventory.items();
    for (const armorName of priority) {
      const piece = items.find((i) => i.name === armorName);
      if (piece) {
        try {
          await bot.equip(piece, slot);
        } catch {}
        break;
      }
    }
  }
}

async function attackThreat(bot, logger) {
  // Equip best gear first
  const equipped = await equipBestWeapon(bot);
  if (equipped) logger.info(`Equipped weapon: ${equipped}`);
  await equipArmor(bot);

  const target = getNearestHostile(bot, 16);
  if (!target) {
    return { success: false, reason: "no_threat_found" };
  }

  logger.info(`Attacking ${target.name} (id: ${target.id})`);

  let attackAttempts = 0;
  const MAX_ATTEMPTS = 10;

  while (attackAttempts < MAX_ATTEMPTS) {
    // Re-check entity still exists
    const stillAlive = bot.entities[target.id];
    if (!stillAlive) {
      logger.info(`Target ${target.name} defeated`);
      return { success: true, reason: "target_defeated" };
    }

    const dist = bot.entity.position.distanceTo(target.position);

    if (dist > 3.5) {
      // Move closer
      try {
        const { GoalNear } = require("mineflayer-pathfinder").goals;
        await Promise.race([
          bot.pathfinder.goto(
            new GoalNear(
              target.position.x,
              target.position.y,
              target.position.z,
              2,
            ),
          ),
          sleep(3000), // don't chase forever
        ]);
      } catch {}
    } else {
      // In range — swing
      bot.attack(target);
      attackAttempts++;
      await sleep(600); // ~1 attack per 0.6s
    }
  }

  return { success: false, reason: "combat_timeout" };
}

const FLEE_HEALTH_THRESHOLD = 8; // 4 hearts (health is 0-20)

async function fleeThreat(bot, logger) {
  const threat = getNearestHostile(bot, 16);
  if (!threat) return { success: false, reason: "no_threat" };

  logger.info(`Fleeing from ${threat.name}`);

  const pos = bot.entity.position;
  const threatPos = threat.position;

  // Run in opposite direction from threat
  const fleeX = pos.x + (pos.x - threatPos.x) * 2;
  const fleeZ = pos.z + (pos.z - threatPos.z) * 2;

  try {
    const { GoalNear } = require("mineflayer-pathfinder").goals;
    await Promise.race([
      bot.pathfinder.goto(new GoalNear(fleeX, pos.y, fleeZ, 1)),
      sleep(4000),
    ]);
    return { success: true, reason: "fled" };
  } catch {
    return { success: false, reason: "flee_failed" };
  }
}

module.exports = {
  getNearestHostile,
  equipBestWeapon,
  equipArmor,
  attackThreat,
  fleeThreat,
};
