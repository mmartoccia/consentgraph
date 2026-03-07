# consentgraph

AI agents break trust when they act without permission. Not because they're malicious -- because the authorization boundary was never made explicit. `consentgraph` gives you a simple, auditable way to define exactly what your agent can do autonomously, what requires human approval, and what is permanently off-limits -- in a single JSON file that travels with your deployment.

```python
from consentgraph import check_consent, ConsentGraphConfig

config = ConsentGraphConfig(graph_path="./consent-graph.json")
tier = check_consent("email", "send", confidence=0.9, config=config)
# → "VISIBLE"  (execute, then notify operator)
```

---

## Install

```bash
pip install consentgraph
# With MCP server support:
pip install "consentgraph[mcp]"
```

---

## The 4-Tier Model

Every action resolves to exactly one tier. The engine checks lists in priority order: **blocked → autonomous → requires_approval → unlisted**.

| Tier | What it means | Agent behavior |
|------|--------------|----------------|
| **SILENT** | Pre-approved. Operator trusts this unconditionally. | Execute. Log it. No notification. |
| **VISIBLE** | Allowed at high confidence (≥ 0.85). | Execute, then notify operator: "I did X because Y." |
| **FORCED** | Allowed but needs explicit approval. | Stop. Surface to operator. Wait for response. |
| **BLOCKED** | Absolute prohibition. Never execute. | Refuse. Alert operator that the attempt was made. |

The `confidence` parameter is the agent's self-reported confidence that the action matches operator intent. High confidence on a `requires_approval` action yields VISIBLE; low confidence yields FORCED. Blocked actions are always blocked, regardless of confidence.

---

## consent-graph.json

Define your domains and actions in a single JSON file:

```json
{
  "domains": {
    "email": {
      "autonomous": ["read", "archive_promo"],
      "requires_approval": ["send", "reply"],
      "blocked": ["delete_all", "bulk_send"],
      "trust_level": "high"
    },
    "filesystem": {
      "autonomous": ["read", "list"],
      "requires_approval": ["write", "create"],
      "blocked": ["delete", "format"],
      "trust_level": "low"
    }
  },
  "consent_decay": {
    "enabled": true,
    "review_interval_days": 30
  }
}
```

See [`examples/consent-graph.example.json`](examples/consent-graph.example.json) for a full 5-domain example with design rationale notes.

**Note on JSON comments:** JSON doesn't support comments natively. The example file uses `"_design_note"` keys for inline documentation -- ConsentGraph ignores unknown keys.

---

## Python API

```python
from consentgraph import check_consent, log_override, ConsentGraphConfig

# Configure once
config = ConsentGraphConfig(
    graph_path="./consent-graph.json",
    log_dir="./logs/",
    confidence_threshold=0.85,  # default
)

# Check before any external action
tier = check_consent("calendar", "create_event", confidence=0.9, config=config)

if tier == "BLOCKED":
    raise PermissionError("Action blocked by consent graph")
elif tier == "FORCED":
    # surface approval UI to operator, await response
    ...
elif tier == "VISIBLE":
    do_action()
    notify_operator("Created calendar event because user requested it.")
else:  # SILENT
    do_action()

# Log when a human overrides a consent decision
log_override(
    domain="calendar",
    action="create_event",
    reason="Operator approved via Slack button",
    operator_decision="approved",
    config=config,
)
```

### ConsentGraphConfig defaults

| Parameter | Default | Description |
|-----------|---------|-------------|
| `graph_path` | `~/.consentgraph/consent-graph.json` | Path to consent graph |
| `log_dir` | `~/.consentgraph/logs/` | Audit log directory |
| `confidence_threshold` | `0.85` | Min confidence for VISIBLE vs FORCED |

---

## CLI

```bash
# Create a starter consent-graph.json
consentgraph init

# Check consent for an action
consentgraph check email send --confidence 0.9

# Print graph summary
consentgraph summary

# Validate graph schema
consentgraph validate

# Check if graph needs review (decay)
consentgraph decay

# Analyze override patterns
consentgraph overrides

# Override graph location
consentgraph --graph /path/to/consent-graph.json summary
```

---

## MCP Server

ConsentGraph ships an MCP server that exposes `check_consent` as a native tool. Any MCP-compatible framework (LangChain, CrewAI, Claude Desktop, custom) can call it.

**Start the server:**
```bash
consentgraph mcp
# or
python -m "consentgraph.mcp_server
```

**MCP client config (e.g. Claude Desktop):**
```json
{
  "mcpServers": {
    "consentgraph": {
      "command": "consentgraph",
      "args": ["mcp"],
      "env": {
        "CONSENTGRAPH_GRAPH_PATH": "/path/to/consent-graph.json"
      }
    }
  }
}
```

**Tool: `check_consent`**

Input:
```json
{
  "domain": "email",
  "action": "send",
  "confidence": 0.9
}
```

Output:
```json
{
  "tier": "VISIBLE",
  "domain": "email",
  "action": "send",
  "confidence": 0.9,
  "guidance": "Proceed, then notify the operator."
}
```

---

## Schema Validation

```python
from consentgraph import validate_graph
import json

with open("consent-graph.json") as f:
    raw = json.load(f)

graph = validate_graph(raw)  # raises pydantic.ValidationError if invalid
print(f"{len(graph.domains)} domains configured")
```

Or via CLI:
```bash
consentgraph validate
```

---

## Audit Trail

Every consent check is logged to `{log_dir}/consent-attempts.jsonl`. Every human override is logged to `{log_dir}/consent-overrides.jsonl`.

```jsonl
{"timestamp": "2025-01-15T14:23:01", "domain": "email", "action": "send", "confidence": 0.9, "tier": "VISIBLE", "reason": "high_confidence_approval"}
```

Use the override log to identify patterns and refine your graph:

```bash
consentgraph overrides
# → "email/send: approved 5x → consider upgrading to autonomous"
```

---

## Why This Matters

Enterprise and government deployments of AI agents face a common failure mode: the authorization boundary is implicit, embedded in prompts or agent code, invisible to auditors, and impossible to update without a code deploy. When something goes wrong -- and it will -- there's no audit trail and no clear policy to point to.

ConsentGraph makes the boundary explicit, version-controlled, human-readable, and independently auditable. The consent graph is the policy. The audit log is the evidence. The override log is the feedback loop that improves the policy over time.

For regulated industries, this pattern maps directly onto existing control frameworks (SOC 2 access controls, FedRAMP least-privilege, NIST AI RMF). The consent graph is a machine-readable policy artifact that compliance teams can review without reading agent code.

---

## Examples

| File | Description |
|------|-------------|
| [`examples/consent-graph.example.json`](examples/consent-graph.example.json) | Full 5-domain starter example with design rationale notes |
| [`examples/aws-ecs-deployment-agent.json`](examples/aws-ecs-deployment-agent.json) | AWS ECS deployment agent (ECS, ECR, CloudWatch, EC2, RDS, S3, IAM) |
| [`examples/aws-cost-optimizer-agent.json`](examples/aws-cost-optimizer-agent.json) | AWS cost optimization agent (Cost Explorer, Trusted Advisor, Compute Optimizer) |
| [`examples/k8s-ops-agent.json`](examples/k8s-ops-agent.json) | Kubernetes ops agent (namespaces, deployments, services, RBAC) |
| [`examples/multi-agent-orchestrator.json`](examples/multi-agent-orchestrator.json) | Cloud ops orchestrator that delegates to specialist sub-agents (v0.2) |
| [`examples/gcc-azure-gov-agent.json`](examples/gcc-azure-gov-agent.json) | Azure Government cloud agent -- FedRAMP High, IL4 scoped, 9 domains (v0.2) |
| [`examples/cmmc-l3-devops-agent.json`](examples/cmmc-l3-devops-agent.json) | CMMC Level 3 DevOps pipeline agent -- NIST 800-171/172 control mappings (v0.2) |

### Multi-Agent Composition

In complex deployments, a single agent with broad permissions is a liability. ConsentGraph v0.2 supports an orchestrator pattern: a narrow orchestrator agent reads state and delegates to specialist sub-agents, each governed by their own consent graph. The orchestrator's `delegation` block declares which agents it trusts, which domains it may invoke on their behalf, and whether each delegation requires human approval. `max_delegation_depth: 1` prevents chain delegation (orchestrator → sub-agent → sub-sub-agent), which would create audit-trail gaps.

```json
"delegation": {
  "trusted_agents": [
    {
      "agent_id": "deployment-agent",
      "graph_path": "examples/aws-ecs-deployment-agent.json",
      "domains_allowed": ["ecs", "ecr"],
      "requires_approval": true
    }
  ],
  "max_delegation_depth": 1
}
```

See [`examples/multi-agent-orchestrator.json`](examples/multi-agent-orchestrator.json) for a full cloud ops orchestrator delegating to deployment, cost, and security scanner sub-agents.

### Compliance Profiles

The `compliance_profile` field in metadata names the framework the graph was authored against (e.g. `"FedRAMP-High"`, `"CMMC-L3"`, `"SOC2-Type2"`). Each domain's `control_mappings` field lists the NIST 800-53 or 800-171 control families that informed its autonomous/requires_approval/blocked split (e.g. `["AC-6", "CM-7", "AU-2"]`). These fields are informational -- the runtime ignores them -- but they give compliance auditors a direct line from agent behavior to the specific controls that justify it. For regulated deployments, the consent graph becomes a machine-readable policy artifact that your AO, ISSO, or auditor can review without reading agent code.

---

## Project Status

v0.1.0 -- production logic extracted and packaged. API is stable. MCP server is functional. Breaking changes will be versioned.

**Roadmap:**
- Async support for `check_consent`
- Time-window constraints (e.g., "only during business hours")
- Graph inheritance (base + environment overrides)
- Multi-agent delegation (orchestrator → sub-agent consent chains)
- Compliance profiles (FedRAMP, CMMC, SOC2 overlays)
- Web UI for graph editing

Contributions welcome.
