"""
Sales Qualification Agent for TinyContext.

Implements BANT, MEDDIC, and other qualification frameworks.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
import json

from .base_sales_agent import BaseSalesAgent, SalesContext
from ..loader import Prompts


class QualificationFramework(Enum):
    """Supported qualification frameworks."""
    BANT = "bant"  # Budget, Authority, Need, Timeline
    MEDDIC = "meddic"  # Metrics, Economic buyer, Decision criteria, Decision process, Identify pain, Champion
    CHAMP = "champ"  # Challenges, Authority, Money, Prioritization
    GPCTBA_CI = "gpctba_ci"  # Goals, Plans, Challenges, Timeline, Budget, Authority, Consequences, Implications
    CUSTOM = "custom"


@dataclass
class QualificationCriteria:
    """Criteria for lead qualification."""
    framework: QualificationFramework
    min_score: float = 60.0
    required_fields: List[str] = None
    scoring_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = self._get_default_fields()
        if self.scoring_weights is None:
            self.scoring_weights = self._get_default_weights()
    
    def _get_default_fields(self) -> List[str]:
        """Get default required fields based on framework."""
        if self.framework == QualificationFramework.BANT:
            return ["budget", "authority", "need", "timeline"]
        elif self.framework == QualificationFramework.MEDDIC:
            return ["metrics", "economic_buyer", "decision_criteria", "decision_process", "pain_points", "champion"]
        elif self.framework == QualificationFramework.CHAMP:
            return ["challenges", "authority", "money", "prioritization"]
        else:
            return ["email", "company", "title"]
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Get default scoring weights."""
        if self.framework == QualificationFramework.BANT:
            return {"budget": 0.3, "authority": 0.25, "need": 0.25, "timeline": 0.2}
        elif self.framework == QualificationFramework.MEDDIC:
            return {
                "metrics": 0.15, "economic_buyer": 0.2, "decision_criteria": 0.15,
                "decision_process": 0.15, "pain_points": 0.2, "champion": 0.15
            }
        else:
            return {"default": 1.0}


class SalesQualificationAgent(BaseSalesAgent):
    """
    Agent specialized in lead qualification using various frameworks.
    
    Features:
    - Multiple qualification frameworks (BANT, MEDDIC, etc.)
    - Configurable scoring thresholds
    - Automatic lead routing based on scores
    - Integration with CRM for lead updates
    """
    
    def __init__(
        self,
        name: str = "QualificationAgent",
        framework: QualificationFramework = QualificationFramework.BANT,
        custom_criteria: Optional[QualificationCriteria] = None
    ):
        """
        Initialize qualification agent.
        
        Args:
            name: Agent name
            framework: Qualification framework to use
            custom_criteria: Custom qualification criteria
        """
        prompts = Prompts(
            system=f"""You are a sales qualification expert using the {framework.value.upper()} framework.
            Analyze leads thoroughly and provide accurate qualification scores.
            Focus on identifying high-value opportunities and filtering out poor fits.""",
            
            reasoning_template="""Analyzing lead for qualification:
            Lead Data: {lead_data}
            Framework: {framework}
            Required Fields: {required_fields}
            
            Let me evaluate each criterion...""",
            
            action_template="""Qualification Result:
            Score: {score}/100
            Status: {status}
            Missing Information: {missing_fields}
            Recommendations: {recommendations}"""
        )
        
        super().__init__(
            name=name,
            role="qualifier",
            persona="Expert in lead qualification and scoring",
            prompts=prompts
        )
        
        # Qualification configuration
        self.framework = framework
        self.criteria = custom_criteria or QualificationCriteria(framework)
        
        # Scoring models for different frameworks
        self.scoring_models = {
            QualificationFramework.BANT: self._score_bant,
            QualificationFramework.MEDDIC: self._score_meddic,
            QualificationFramework.CHAMP: self._score_champ,
            QualificationFramework.GPCTBA_CI: self._score_gpctba_ci
        }
        
        # Lead routing rules
        self.routing_rules = {
            "high": {"min_score": 80, "route_to": "sales_team"},
            "medium": {"min_score": 60, "route_to": "nurture_campaign"},
            "low": {"min_score": 0, "route_to": "marketing_automation"}
        }
    
    async def qualify_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Qualify a lead using the configured framework.
        
        Args:
            lead_data: Lead information to qualify
            
        Returns:
            Qualification result with score and recommendations
        """
        # Process lead through base class
        await self.process_lead(lead_data)
        
        # Enrich data if needed
        enriched_data = self.enrich_lead_data(lead_data)
        
        # Check for required fields
        missing_fields = self._check_required_fields(enriched_data)
        
        # Calculate qualification score
        score = self._calculate_qualification_score(enriched_data)
        self.sales_context.qualification_score = score
        
        # Determine qualification status
        status = self._determine_status(score)
        self.sales_context.stage = status
        
        # Generate recommendations
        recommendations = self._generate_recommendations(enriched_data, score, missing_fields)
        
        # Determine routing
        route_to = self._determine_routing(score)
        
        # Update metrics
        self.update_metrics(status, score)
        
        # Build result
        result = {
            "lead_id": enriched_data.get("id", "unknown"),
            "framework": self.framework.value,
            "score": score,
            "status": status,
            "missing_fields": missing_fields,
            "recommendations": recommendations,
            "route_to": route_to,
            "detailed_scores": self._get_detailed_scores(enriched_data),
            "agent": self.name,
            "context": self.sales_context.to_dict()
        }
        
        # Add interaction to history
        self.sales_context.add_interaction("qualification_complete", result)
        
        return result
    
    def _check_required_fields(self, lead_data: Dict[str, Any]) -> List[str]:
        """Check for missing required fields."""
        missing = []
        for field in self.criteria.required_fields:
            if field not in lead_data or not lead_data[field]:
                missing.append(field)
        return missing
    
    def _calculate_qualification_score(self, lead_data: Dict[str, Any]) -> float:
        """
        Calculate qualification score based on framework.
        
        Args:
            lead_data: Lead information
            
        Returns:
            Score between 0-100
        """
        # Get scoring function for framework
        scoring_func = self.scoring_models.get(
            self.framework,
            self._score_custom
        )
        
        return scoring_func(lead_data)
    
    def _score_bant(self, lead_data: Dict[str, Any]) -> float:
        """Score using BANT framework."""
        score = 0.0
        weights = self.criteria.scoring_weights
        
        # Budget
        if "budget" in lead_data:
            budget = lead_data["budget"]
            if isinstance(budget, (int, float)) and budget > 0:
                if budget >= 100000:
                    score += weights["budget"] * 100
                elif budget >= 50000:
                    score += weights["budget"] * 75
                elif budget >= 10000:
                    score += weights["budget"] * 50
                else:
                    score += weights["budget"] * 25
        
        # Authority
        if "authority" in lead_data or "title" in lead_data:
            title = lead_data.get("authority", lead_data.get("title", "")).lower()
            if any(word in title for word in ["ceo", "cto", "cfo", "vp", "director"]):
                score += weights["authority"] * 100
            elif any(word in title for word in ["manager", "head", "lead"]):
                score += weights["authority"] * 60
            else:
                score += weights["authority"] * 20
        
        # Need
        if "need" in lead_data or "pain_points" in lead_data:
            need = lead_data.get("need", lead_data.get("pain_points"))
            if need:
                score += weights["need"] * 80  # Has expressed need
        
        # Timeline
        if "timeline" in lead_data:
            timeline = lead_data["timeline"].lower() if isinstance(lead_data["timeline"], str) else ""
            if any(word in timeline for word in ["immediate", "asap", "urgent", "this month"]):
                score += weights["timeline"] * 100
            elif any(word in timeline for word in ["quarter", "q1", "q2", "3 months"]):
                score += weights["timeline"] * 75
            elif any(word in timeline for word in ["year", "6 months"]):
                score += weights["timeline"] * 50
            else:
                score += weights["timeline"] * 25
        
        return min(score, 100.0)
    
    def _score_meddic(self, lead_data: Dict[str, Any]) -> float:
        """Score using MEDDIC framework."""
        score = 0.0
        weights = self.criteria.scoring_weights
        
        # Metrics - quantifiable goals
        if "metrics" in lead_data or "goals" in lead_data:
            metrics = lead_data.get("metrics", lead_data.get("goals"))
            if metrics and any(char.isdigit() for char in str(metrics)):
                score += weights["metrics"] * 80
        
        # Economic buyer
        if "economic_buyer" in lead_data or self._is_economic_buyer(lead_data.get("title", "")):
            score += weights["economic_buyer"] * 100
        
        # Decision criteria
        if "decision_criteria" in lead_data:
            criteria = lead_data["decision_criteria"]
            if isinstance(criteria, list) and len(criteria) > 2:
                score += weights["decision_criteria"] * 80
            elif criteria:
                score += weights["decision_criteria"] * 50
        
        # Decision process
        if "decision_process" in lead_data:
            score += weights["decision_process"] * 70
        
        # Identify pain
        if "pain_points" in lead_data:
            pain_points = lead_data["pain_points"]
            if isinstance(pain_points, list) and len(pain_points) > 1:
                score += weights["pain_points"] * 90
            elif pain_points:
                score += weights["pain_points"] * 60
        
        # Champion
        if "champion" in lead_data or "internal_advocate" in lead_data:
            score += weights["champion"] * 85
        
        return min(score, 100.0)
    
    def _score_champ(self, lead_data: Dict[str, Any]) -> float:
        """Score using CHAMP framework."""
        score = 0.0
        
        # Challenges (30%)
        if "challenges" in lead_data or "pain_points" in lead_data:
            challenges = lead_data.get("challenges", lead_data.get("pain_points"))
            if challenges:
                score += 25
        
        # Authority (25%)
        if self._has_authority(lead_data):
            score += 20
        
        # Money (25%)
        if "budget" in lead_data and lead_data["budget"]:
            score += 20
        
        # Prioritization (20%)
        if "priority" in lead_data or "timeline" in lead_data:
            priority = lead_data.get("priority", lead_data.get("timeline", ""))
            if any(word in str(priority).lower() for word in ["high", "urgent", "immediate"]):
                score += 20
            else:
                score += 10
        
        return min(score + self.calculate_base_score(lead_data), 100.0)
    
    def _score_gpctba_ci(self, lead_data: Dict[str, Any]) -> float:
        """Score using GPCTBA/C&I framework."""
        score = 0.0
        
        # Goals (15%)
        if "goals" in lead_data:
            score += 15
        
        # Plans (10%)
        if "plans" in lead_data or "strategy" in lead_data:
            score += 10
        
        # Challenges (15%)
        if "challenges" in lead_data:
            score += 15
        
        # Timeline (10%)
        if "timeline" in lead_data:
            score += 10
        
        # Budget (15%)
        if "budget" in lead_data:
            score += 15
        
        # Authority (15%)
        if self._has_authority(lead_data):
            score += 15
        
        # Negative Consequences (10%)
        if "consequences" in lead_data:
            score += 10
        
        # Positive Implications (10%)
        if "implications" in lead_data or "benefits" in lead_data:
            score += 10
        
        return min(score, 100.0)
    
    def _score_custom(self, lead_data: Dict[str, Any]) -> float:
        """Score using custom criteria."""
        return self.calculate_base_score(lead_data)
    
    def _is_economic_buyer(self, title: str) -> bool:
        """Check if title indicates economic buyer."""
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in 
                  ["ceo", "cfo", "owner", "president", "vp finance", "procurement"])
    
    def _has_authority(self, lead_data: Dict[str, Any]) -> bool:
        """Check if lead has decision-making authority."""
        title = lead_data.get("title", "").lower()
        return any(keyword in title for keyword in 
                  ["director", "manager", "head", "lead", "vp", "chief"])
    
    def _determine_status(self, score: float) -> str:
        """Determine qualification status based on score."""
        if score >= 80:
            return "highly_qualified"
        elif score >= self.criteria.min_score:
            return "qualified"
        elif score >= 40:
            return "needs_nurturing"
        else:
            return "disqualified"
    
    def _determine_routing(self, score: float) -> str:
        """Determine where to route the lead."""
        for priority, rule in self.routing_rules.items():
            if score >= rule["min_score"]:
                return rule["route_to"]
        return "archive"
    
    def _generate_recommendations(
        self,
        lead_data: Dict[str, Any],
        score: float,
        missing_fields: List[str]
    ) -> List[str]:
        """Generate recommendations for next steps."""
        recommendations = []
        
        if score >= 80:
            recommendations.append("High-priority lead - assign to senior sales rep immediately")
            recommendations.append("Schedule discovery call within 24 hours")
        elif score >= 60:
            recommendations.append("Qualified lead - assign to sales team")
            recommendations.append("Send personalized follow-up within 48 hours")
            if missing_fields:
                recommendations.append(f"Gather missing information: {', '.join(missing_fields)}")
        elif score >= 40:
            recommendations.append("Add to nurture campaign")
            recommendations.append("Schedule follow-up in 30 days")
            recommendations.append("Send educational content")
        else:
            recommendations.append("Low priority - add to marketing automation")
            recommendations.append("Monitor for engagement signals")
        
        # Specific recommendations based on data
        if "competitor" in lead_data:
            recommendations.append("Prepare competitive analysis")
        
        if lead_data.get("company_size", 0) > 500:
            recommendations.append("Consider enterprise sales approach")
        
        return recommendations
    
    def _get_detailed_scores(self, lead_data: Dict[str, Any]) -> Dict[str, float]:
        """Get detailed scoring breakdown."""
        detailed = {}
        
        if self.framework == QualificationFramework.BANT:
            detailed = {
                "budget": self._score_budget_component(lead_data),
                "authority": self._score_authority_component(lead_data),
                "need": self._score_need_component(lead_data),
                "timeline": self._score_timeline_component(lead_data)
            }
        
        return detailed
    
    def _score_budget_component(self, lead_data: Dict[str, Any]) -> float:
        """Score budget component."""
        if "budget" not in lead_data:
            return 0.0
        budget = lead_data["budget"]
        if isinstance(budget, (int, float)):
            if budget >= 100000:
                return 100.0
            elif budget >= 50000:
                return 75.0
            elif budget >= 10000:
                return 50.0
            else:
                return 25.0
        return 0.0
    
    def _score_authority_component(self, lead_data: Dict[str, Any]) -> float:
        """Score authority component."""
        title = lead_data.get("title", "").lower()
        if any(word in title for word in ["ceo", "cto", "cfo", "vp", "director"]):
            return 100.0
        elif any(word in title for word in ["manager", "head", "lead"]):
            return 60.0
        return 20.0
    
    def _score_need_component(self, lead_data: Dict[str, Any]) -> float:
        """Score need component."""
        if "need" in lead_data or "pain_points" in lead_data:
            return 80.0
        return 0.0
    
    def _score_timeline_component(self, lead_data: Dict[str, Any]) -> float:
        """Score timeline component."""
        if "timeline" not in lead_data:
            return 0.0
        timeline = str(lead_data["timeline"]).lower()
        if any(word in timeline for word in ["immediate", "asap", "urgent"]):
            return 100.0
        elif any(word in timeline for word in ["quarter", "3 months"]):
            return 75.0
        elif any(word in timeline for word in ["6 months", "year"]):
            return 50.0
        return 25.0
    
    def set_custom_routing(self, routing_rules: Dict[str, Dict[str, Any]]):
        """
        Set custom routing rules.
        
        Args:
            routing_rules: Dictionary of routing rules by priority
        """
        self.routing_rules = routing_rules
    
    def export_qualification_report(self, lead_data: Dict[str, Any]) -> str:
        """
        Export a detailed qualification report.
        
        Args:
            lead_data: Lead information
            
        Returns:
            Formatted qualification report
        """
        result = self.qualify_lead(lead_data)
        
        report = f"""
LEAD QUALIFICATION REPORT
========================
Lead ID: {result['lead_id']}
Framework: {result['framework'].upper()}
Score: {result['score']}/100
Status: {result['status']}
Route To: {result['route_to']}

DETAILED SCORES:
{json.dumps(result['detailed_scores'], indent=2)}

MISSING INFORMATION:
{', '.join(result['missing_fields']) if result['missing_fields'] else 'None'}

RECOMMENDATIONS:
{chr(10).join(f"- {rec}" for rec in result['recommendations'])}

AGENT METRICS:
{json.dumps(self.get_performance_summary()['metrics'], indent=2)}
"""
        return report