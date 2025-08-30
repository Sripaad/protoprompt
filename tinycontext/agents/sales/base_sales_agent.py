"""
Base Sales Agent for TinyContext.

Provides common functionality for all sales-specific agents.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

from ..loader import TinyPerson, Prompts


@dataclass
class SalesContext:
    """Context specific to sales operations."""
    lead_data: Dict[str, Any] = field(default_factory=dict)
    company_data: Dict[str, Any] = field(default_factory=dict)
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)
    qualification_score: float = 0.0
    stage: str = "new"
    integrations_available: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_interaction(self, interaction_type: str, details: Any):
        """Add an interaction to history."""
        self.interaction_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "details": details
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "lead_data": self.lead_data,
            "company_data": self.company_data,
            "interaction_history": self.interaction_history,
            "qualification_score": self.qualification_score,
            "stage": self.stage,
            "integrations_available": self.integrations_available,
            "metadata": self.metadata
        }


class BaseSalesAgent(TinyPerson):
    """
    Base class for sales-specific agents.
    
    Extends TinyPerson with sales-specific capabilities like
    lead scoring, CRM integration, and pipeline management.
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        persona: str = "",
        prompts: Optional[Prompts] = None,
        sales_context: Optional[SalesContext] = None
    ):
        """
        Initialize base sales agent.
        
        Args:
            name: Agent name
            role: Agent role in sales process
            persona: Agent personality/expertise
            prompts: Prompt configuration
            sales_context: Sales-specific context
        """
        super().__init__(name, role, persona, prompts or Prompts())
        
        # Sales-specific attributes
        self.sales_context = sales_context or SalesContext()
        self.capabilities = self._get_base_capabilities()
        self.scoring_models = {}
        self.integration_configs = {}
        
        # Performance tracking
        self.metrics = {
            "leads_processed": 0,
            "qualified_leads": 0,
            "conversion_rate": 0.0,
            "avg_score": 0.0
        }
    
    def _get_base_capabilities(self) -> List[str]:
        """Get base capabilities for sales agents."""
        return [
            "lead_scoring",
            "data_enrichment",
            "crm_sync",
            "pipeline_management",
            "metrics_tracking"
        ]
    
    async def process_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a lead through the sales pipeline.
        
        Args:
            lead_data: Lead information
            
        Returns:
            Processing result
        """
        # Update context
        self.sales_context.lead_data = lead_data
        self.sales_context.add_interaction("lead_received", lead_data)
        
        # Update metrics
        self.metrics["leads_processed"] += 1
        
        # Base processing (to be overridden by subclasses)
        result = {
            "agent": self.name,
            "role": self.role,
            "lead_id": lead_data.get("id", "unknown"),
            "processed_at": datetime.now().isoformat(),
            "context": self.sales_context.to_dict()
        }
        
        return result
    
    def enrich_lead_data(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich lead data with additional information.
        
        Args:
            lead_data: Basic lead information
            
        Returns:
            Enriched lead data
        """
        enriched = dict(lead_data)
        
        # Add computed fields
        if "email" in lead_data:
            domain = lead_data["email"].split("@")[-1]
            enriched["company_domain"] = domain
            enriched["is_corporate"] = not any(
                provider in domain for provider in 
                ["gmail", "yahoo", "hotmail", "outlook"]
            )
        
        # Add to context
        self.sales_context.lead_data = enriched
        
        return enriched
    
    def calculate_base_score(self, lead_data: Dict[str, Any]) -> float:
        """
        Calculate a base qualification score.
        
        Args:
            lead_data: Lead information
            
        Returns:
            Base score (0-100)
        """
        score = 0.0
        
        # Basic scoring logic
        if lead_data.get("is_corporate", False):
            score += 20
        
        if lead_data.get("title"):
            title = lead_data["title"].lower()
            if any(keyword in title for keyword in ["director", "vp", "chief", "head"]):
                score += 30
            elif any(keyword in title for keyword in ["manager", "lead"]):
                score += 20
        
        if lead_data.get("company_size", 0) > 100:
            score += 20
        
        if lead_data.get("budget"):
            score += 30
        
        return min(score, 100.0)
    
    def get_integration_requirements(self) -> List[str]:
        """
        Get required integrations for this agent.
        
        Returns:
            List of integration identifiers
        """
        return []
    
    def validate_integration(self, integration_name: str) -> bool:
        """
        Validate if an integration is available and configured.
        
        Args:
            integration_name: Name of the integration
            
        Returns:
            True if integration is ready
        """
        return integration_name in self.sales_context.integrations_available
    
    def update_metrics(self, outcome: str, score: float = 0.0):
        """
        Update agent performance metrics.
        
        Args:
            outcome: Outcome of processing (qualified/disqualified)
            score: Qualification score if applicable
        """
        if outcome == "qualified":
            self.metrics["qualified_leads"] += 1
        
        # Update conversion rate
        if self.metrics["leads_processed"] > 0:
            self.metrics["conversion_rate"] = (
                self.metrics["qualified_leads"] / self.metrics["leads_processed"]
            )
        
        # Update average score
        if score > 0:
            current_avg = self.metrics["avg_score"]
            n = self.metrics["leads_processed"]
            self.metrics["avg_score"] = ((current_avg * (n - 1)) + score) / n
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary for this agent.
        
        Returns:
            Performance metrics dictionary
        """
        return {
            "agent": self.name,
            "role": self.role,
            "metrics": self.metrics,
            "active_integrations": self.sales_context.integrations_available,
            "current_stage": self.sales_context.stage
        }
    
    async def handoff_to_agent(self, target_agent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handoff processing to another agent.
        
        Args:
            target_agent: Name of target agent
            context: Context to pass
            
        Returns:
            Handoff result
        """
        handoff_data = {
            "from_agent": self.name,
            "to_agent": target_agent,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "sales_context": self.sales_context.to_dict()
        }
        
        self.sales_context.add_interaction("handoff", handoff_data)
        
        return handoff_data
    
    def format_for_crm(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format lead data for CRM systems.
        
        Args:
            lead_data: Raw lead data
            
        Returns:
            CRM-formatted data
        """
        # Standard CRM fields mapping
        crm_data = {
            "firstName": lead_data.get("first_name", ""),
            "lastName": lead_data.get("last_name", ""),
            "email": lead_data.get("email", ""),
            "phone": lead_data.get("phone", ""),
            "company": lead_data.get("company", ""),
            "title": lead_data.get("title", ""),
            "leadSource": lead_data.get("source", "API"),
            "status": self.sales_context.stage,
            "score": self.sales_context.qualification_score,
            "customFields": {
                "processed_by": self.name,
                "processed_at": datetime.now().isoformat(),
                "interactions": len(self.sales_context.interaction_history)
            }
        }
        
        return crm_data