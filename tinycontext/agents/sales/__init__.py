"""
Sales-specific agents for TinyContext.

This module provides specialized agents for sales automation including
lead qualification, generation, and integration discovery.
"""

from .base_sales_agent import BaseSalesAgent
from .qualification_agent import SalesQualificationAgent
from .lead_gen_agent import LeadGenerationAgent
from .integration_discovery import IntegrationDiscoveryAgent
from .outreach_agent import OutreachAgent

__all__ = [
    "BaseSalesAgent",
    "SalesQualificationAgent", 
    "LeadGenerationAgent",
    "IntegrationDiscoveryAgent",
    "OutreachAgent"
]