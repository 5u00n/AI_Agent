---
source_file: "agent/config.py"
type: "code"
community: "agent.py"
location: "L170"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/agentpy
---

# load_config()

## Connections
- [[.default()]] - `calls` [EXTRACTED]
- [[AgentConfig]] - `references` [EXTRACTED]
- [[BudgetConfig]] - `indirect_call` [INFERRED]
- [[LLMConfig]] - `indirect_call` [INFERRED]
- [[Load agent config from a YAML file. Returns defaults if file missing.]] - `rationale_for` [EXTRACTED]
- [[MCPConfig]] - `calls` [EXTRACTED]
- [[MCPServerConfig]] - `calls` [EXTRACTED]
- [[Path_1]] - `references` [EXTRACTED]
- [[SafetyConfig]] - `indirect_call` [INFERRED]
- [[TestPolicyConfig]] - `indirect_call` [INFERRED]
- [[UIConfig]] - `indirect_call` [INFERRED]
- [[__init__.py]] - `imports` [EXTRACTED]
- [[_build_dataclass()]] - `calls` [EXTRACTED]
- [[cli.py]] - `imports` [EXTRACTED]
- [[config.py]] - `contains` [EXTRACTED]
- [[ensure_default_config()]] - `calls` [EXTRACTED]
- [[test_agent.py]] - `imports` [EXTRACTED]
- [[test_load_config_supports_provider_switch()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/agentpy