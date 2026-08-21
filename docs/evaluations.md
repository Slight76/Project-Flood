# Behavioral Evaluations

[`evals/cases.yaml`](../evals/cases.yaml) is the versioned behavior and adversarial corpus. Structural CI validates its schema and the deterministic code paths. Model behavior must still be exercised in each supported harness because routing and available tools are runtime-dependent.

For each case, capture:

- VS Code/Copilot version and harness;
- discovered agents, skills, hooks, and tools;
- model and relevant policy settings;
- outcome against every expected and forbidden behavior;
- Agent Debug flow, tool calls, token totals, errors, and approval decisions;
- any corrective configuration change.

Never store prompts or debug exports that contain credentials, personal data, private source, or production values. Promote only durable, verified lessons through Flood Librarian.
