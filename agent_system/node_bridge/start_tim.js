require("../../bots/agents/tim");

const fs = require("fs");
const LOCK_FILE = "/tmp/tim.lock";

if (fs.existsSync(LOCK_FILE)) {
  console.error(
    "Tim is already running! Delete /tmp/tim.lock if this is wrong.",
  );
  process.exit(1);
}

fs.writeFileSync(LOCK_FILE, String(process.pid));

process.on("exit", () => {
  try {
    fs.unlinkSync(LOCK_FILE);
  } catch {}
});
process.on("SIGINT", () => process.exit());
process.on("SIGTERM", () => process.exit());
