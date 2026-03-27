Issue: prevent gather thrashing on unreachable wood and gather enough logs to build

Success criteria:

- Tim does not repeatedly switch between explore and gather without making progress
- gatherWood succeeds at least once during the runtime window
- runtime shows current total log count increasing above 0
- Tim continues gathering until total log count reaches the build threshold
- runtime shows a goal switch to build_column after enough logs are collected

Editable files:

- bots/capabilities/movement.js
- bots/agents/tim.js
- bots/capabilities/gather.js

Max attempts:

- 6

Runtime seconds:

- 30
