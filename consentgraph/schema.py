"""
ConsentGraph Schema

Pydantic v2 models for the consent-graph.json format.
Use validate_graph() to verify a graph dict against these models.

v0.2 additions (all optional, fully backward-compatible with v0.1 graphs):
  - ConsentDomain: control_mappings, delegation_allowed
  - ConsentGraphMetadata: compliance_profile, agent_id
  - BoundaryConfig: allowed_tenants, allowed_endpoints, deny_cross_boundary
  - DelegationTarget + DelegationConfig: trusted_agents, max_delegation_depth
  - ConsentGraph: boundary, delegation
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ConsentDomain(BaseModel):
    """
    Rules for a single domain (e.g. "email", "calendar").

    Lists are matched by exact string. The resolution order is:
        blocked > autonomous > requires_approval > unlisted

    v0.2 additions:
        control_mappings: NIST 800-53/171 control family references (e.g. ["AC-6", "CM-7"])
        delegation_allowed: whether an orchestrator may invoke this domain on behalf of a sub-agent
    """
    autonomous: list[str] = Field(
        default_factory=list,
        description="Actions the agent may execute without notification.",
    )
    requires_approval: list[str] = Field(
        default_factory=list,
        description=(
            "Actions that require notification (high confidence) or explicit "
            "approval (low confidence) before execution."
        ),
    )
    blocked: list[str] = Field(
        default_factory=list,
        description="Actions the agent must never execute, regardless of confidence.",
    )
    trust_level: str = Field(
        default="medium",
        description="Informational trust label: low | medium | high | critical",
    )
    # v0.2 fields
    control_mappings: Optional[list[str]] = Field(
        default=None,
        description=(
            "v0.2: Optional NIST 800-53/171 control family references for this domain "
            "(e.g. ['AC-6', 'CM-7', 'AU-2']). Informational -- used by auditors and "
            "compliance tooling to map graph rules to specific controls."
        ),
    )
    delegation_allowed: Optional[bool] = Field(
        default=None,
        description=(
            "v0.2: If true, an orchestrator agent may invoke actions in this domain "
            "on behalf of a delegating agent. Defaults to false when absent."
        ),
    )

    @model_validator(mode="after")
    def no_overlap(self) -> "ConsentDomain":
        """Warn if any action appears in multiple lists (last-wins in runtime, but is a config bug)."""
        auto_set = set(self.autonomous)
        approval_set = set(self.requires_approval)
        blocked_set = set(self.blocked)

        overlap_ab = auto_set & blocked_set
        overlap_aa = auto_set & approval_set
        overlap_ba = blocked_set & approval_set

        issues = []
        if overlap_ab:
            issues.append(f"Actions in both autonomous and blocked: {overlap_ab}")
        if overlap_aa:
            issues.append(f"Actions in both autonomous and requires_approval: {overlap_aa}")
        if overlap_ba:
            issues.append(f"Actions in both blocked and requires_approval: {overlap_ba}")

        if issues:
            raise ValueError("Overlapping action lists: " + "; ".join(issues))
        return self


class ConsentDecay(BaseModel):
    """Configuration for periodic consent graph review."""
    enabled: bool = False
    review_interval_days: int = Field(
        default=30,
        ge=1,
        description="Days between mandatory reviews of the consent graph.",
    )


class BoundaryConfig(BaseModel):
    """
    v0.2: Cloud boundary constraints to prevent cross-tenant or cross-environment spillover.

    Example -- GCC High / Azure Government agent that must never touch commercial endpoints::

        {
          "allowed_tenants": ["my-agency.onmicrosoft.us"],
          "allowed_endpoints": ["*.azure.us", "*.microsoftonline.us"],
          "deny_cross_boundary": true
        }
    """
    allowed_tenants: Optional[list[str]] = Field(
        default=None,
        description="Tenant IDs or domain patterns this agent is permitted to operate in.",
    )
    allowed_endpoints: Optional[list[str]] = Field(
        default=None,
        description="Endpoint patterns (glob-style) this agent may call.",
    )
    deny_cross_boundary: bool = Field(
        default=False,
        description=(
            "If true, the runtime must reject any action that would cross into a "
            "tenant or endpoint not in the allow-lists."
        ),
    )


class DelegationTarget(BaseModel):
    """
    v0.2: A single trusted sub-agent entry in an orchestrator's delegation config.

    Fields:
        agent_id:          Identifier matching the sub-agent's own consent graph agent_id.
        graph_path:        Path or URI to the sub-agent's consent graph (for validation).
        domains_allowed:   Which domains the orchestrator may invoke on this agent's behalf.
        requires_approval: If true, every delegation to this agent must be approved by a human
                           before execution (regardless of the sub-agent's own tier).
    """
    agent_id: str = Field(description="Identifier of the trusted sub-agent.")
    graph_path: str = Field(description="Path or URI to the sub-agent's consent graph file.")
    domains_allowed: list[str] = Field(
        default_factory=list,
        description="Domains the orchestrator is permitted to delegate to this agent.",
    )
    requires_approval: bool = Field(
        default=False,
        description="If true, all delegations to this agent require human approval first.",
    )


class DelegationConfig(BaseModel):
    """
    v0.2: Orchestrator-level delegation configuration.

    Only needed on orchestrator agents. Sub-agents that are purely leaf nodes do not
    need this section. Setting max_delegation_depth=1 (the default) prevents chain
    delegation (orchestrator → sub-agent → sub-sub-agent) which creates audit-trail gaps.

    Example::

        {
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
    """
    trusted_agents: list[DelegationTarget] = Field(
        default_factory=list,
        description="Agents this orchestrator is permitted to delegate to.",
    )
    max_delegation_depth: int = Field(
        default=1,
        ge=1,
        description=(
            "Maximum allowed chain length for delegation. 1 = orchestrator may delegate "
            "to direct sub-agents only (no chained delegation). Increase with caution."
        ),
    )


class ConsentGraphMetadata(BaseModel):
    """
    Optional metadata block for documentation and tooling.

    v0.2 additions:
        compliance_profile: named compliance framework this graph was designed against
        agent_id:           identifier for this agent in a multi-agent fleet
    """
    version: str = "0.1.0"
    description: Optional[str] = None
    owner: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # v0.2 fields
    compliance_profile: Optional[str] = Field(
        default=None,
        description=(
            "v0.2: Named compliance framework this graph was authored against. "
            "Examples: 'FedRAMP-High', 'CMMC-L3', 'SOC2-Type2', 'IL4', 'commercial'. "
            "Informational -- used by auditors and overlay tooling."
        ),
    )
    agent_id: Optional[str] = Field(
        default=None,
        description=(
            "v0.2: Stable identifier for this agent in a multi-agent fleet. "
            "Must match the agent_id referenced in any orchestrator's DelegationTarget."
        ),
    )


class ConsentGraph(BaseModel):
    """
    Root model for consent-graph.json.

    Example minimal graph::

        {
          "domains": {
            "email": {
              "autonomous": ["read", "archive_promo"],
              "requires_approval": ["send"],
              "blocked": ["delete_all"],
              "trust_level": "high"
            }
          },
          "consent_decay": {"enabled": true, "review_interval_days": 30}
        }

    v0.2 additions (all optional, v0.1 graphs remain valid):
        boundary:   Cloud boundary constraints (allowed tenants/endpoints).
        delegation: Orchestrator-only delegation config (trusted sub-agents, depth limit).
    """
    domains: dict[str, ConsentDomain] = Field(
        default_factory=dict,
        description="Map of domain name → domain rules.",
    )
    consent_decay: ConsentDecay = Field(default_factory=ConsentDecay)
    last_reviewed: Optional[str] = Field(
        default=None,
        description="ISO date (YYYY-MM-DD) of last human review.",
    )
    metadata: Optional[ConsentGraphMetadata] = None
    # v0.2 fields
    boundary: Optional[BoundaryConfig] = Field(
        default=None,
        description=(
            "v0.2: Cloud boundary constraints. Define allowed tenants and endpoints to "
            "prevent cross-boundary spillover (e.g., GovCloud agent calling commercial APIs)."
        ),
    )
    delegation: Optional[DelegationConfig] = Field(
        default=None,
        description=(
            "v0.2: Orchestrator delegation config. Present only on orchestrator agents. "
            "Defines trusted sub-agents and delegation depth limits."
        ),
    )


def validate_graph(graph: dict) -> ConsentGraph:
    """
    Validate a consent graph dict against the ConsentGraph schema.

    Args:
        graph: Raw dict (e.g. from json.load()).

    Returns:
        Validated ConsentGraph instance.

    Raises:
        pydantic.ValidationError if the graph is malformed.
    """
    return ConsentGraph.model_validate(graph)
