"""
backend/decision_support/__init__.py
===================================
Resource-Aware Manoeuvre Decision Support Module for ICPS.
Provides candidate avoidance manoeuvre generation, propellant budget validation,
hardware constraint enforcement, and human-in-the-loop approval workflows.
"""

from .models import (
    ManoeuvreOption,
    ManoeuvreProposal,
    ProposalApprovalState,
    SpacecraftConstraints,
)
from .planner import ResourceAwareManoeuvrePlanner

__all__ = [
    "ManoeuvreOption",
    "ManoeuvreProposal",
    "ProposalApprovalState",
    "SpacecraftConstraints",
    "ResourceAwareManoeuvrePlanner",
]
