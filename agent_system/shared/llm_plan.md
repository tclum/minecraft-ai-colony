1. Current diagnosis

- The runtime error "Tim is already running! Delete /tmp/tim.lock if this is wrong." indicates a lockfile or process concurrency issue preventing multiple instances, causing the watchdog Python orchestrator to interpret bot run as failure (return code 1).
- Tim's reconnect logic exits after 5 failed reconnect attempts, which may cause unexpected termination if connectivity is flaky.
- Memory persistence exists but stale active goals are resumed on restart with no clear reset on startup, causing potential goal confusion.
- gatherWood's fallback behavior handles no logs by clearing recent fails but does not try alternative area or re-explore.
- The explore capability always returns after first wood spotted; resumption after failure is handled by switching goals.
- Stuck detection increments on gather failure but no automatic clearing on success or on startup.
- Logging and memory save are comprehensive, aiding observability.
- Overall, the main blocker to reliability seen here is the stale lockfile / multiple bot instance prevention, and partial memory reset on startup.

2. Top 3 recommended code changes

a) Improve startup memory and runtime state reset in bots/agents/tim.js to prevent resuming stale active goals and stuck counts; explicitly clear currentGoal, currentStep, currentTask, goalStatus to "idle" on spawn/startup.

b) Add lockfile removal or detection logic in bots/agents/tim.js before bot creation to handle stale /tmp/tim.lock files gracefully and avoid "Tim already running" error that causes process exit with code 1.

c) Enhance gatherWood fallback in bots/capabilities/gather.js to trigger an explore goal after repeated "no_logs_found" failures, instead of only clearing recentlyFailed set, enabling better recovery and less stuck states.

3. File-by-file patch targets

- bots/agents/tim.js:
  * Add logic on startup/spawn to reset memory goal state and stuckCount.
  * Add code to detect and remove stale lockfile (/tmp/tim.lock) before bot.createBot call or at startup to avoid immediate "already running" error and enable reliable start.
  * Optionally improve reconnect logic to delay exit or reset stuck counters on reconnect.

- bots/capabilities/gather.js:
  * Modify gatherWood to return a specific failure reason "no_logs_found" and let tim.js workerLoop on repeated failures switch goal to "scout_area" (which it does).
  * Possibly add a callback or event from gatherWood failure to trigger goal switch more proactively.

- (Optional) bots/capabilities/movement.js or memory.js core (not provided):
  * No direct changes suggested since current issues are around startup and fallback, but consider later adding more advanced fallback around explore or scout_area goals.

4. Suggested next milestone

- Implement and test robust agent startup that clears stale goals and stuck counters and handles stale lockfiles.
- Verify the Python orchestrator can start Tim reliably without lockfile errors.
- Confirm gatherWood fallback triggers explore goal after no logs consistently.
- Achieve stable run where Tim connects, gathers wood, switches goals on threshold, and stays alive without crashes or disconnects.
- Deliver improved baseline reliability in the existing architecture per current goal.