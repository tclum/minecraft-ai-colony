function getNextStep(memory) {
  const goal = memory.currentGoal;
  if (!goal) return null;

  if (goal.type === "collect_wood") {
    return { type: "gatherWood" };
  }

  if (goal.type === "build_column") {
    return {
      type: "buildColumn",
      height: goal.height || 3,
      block: goal.block || "dirt",
    };
  }

  if (goal.type === "combat") {
    return { type: "attackThreat" };
  }

  if (goal.type === "idle") {
    return { type: "explore", radius: 8 };
  }

  if (goal.type === "scout_area") {
    return { type: "explore", radius: 6 };
  }

  return { type: "explore", radius: 12 };
}

module.exports = { getNextStep };
