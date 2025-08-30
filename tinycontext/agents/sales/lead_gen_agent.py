"""
Lead Generation Agent for TinyContext.

Identifies, enriches, and prioritizes potential prospects.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re

from .base_sales_agent import BaseSalesAgent, SalesContext
from ..loader import Prompts


class LeadSource(Enum):
    """Sources for lead generation."""
    WEB_FORM = "web_form"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    REFERRAL = "referral"
    COLD_OUTREACH = "cold_outreach"
    EVENT = "event"
    PARTNER = "partner"
    INBOUND = "inbound"
    DATABASE = "database"
    API = "api"


@dataclass
class IdealCustomerProfile:
    """Ideal Customer Profile (ICP) definition."""
    industry: List[str] = field(default_factory=list)
    company_size_min: int = 10
    company_size_max: int = 10000
    revenue_min: float = 0
    revenue_max: float = float('inf')
    geography: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    job_titles: List[str] = field(default_factory=list)
    department: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)
    
    def matches(self, prospect_data: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Check if prospect matches ICP.
        
        Returns:
            Tuple of (matches, match_score)
        """
        score = 0.0
        total_criteria = 0
        
        # Industry match
        if self.industry and "industry" in prospect_data:
            total_criteria += 1
            if prospect_data["industry"] in self.industry:
                score += 1.0
        
        # Company size match
        if "company_size" in prospect_data:
            total_criteria += 1
            size = prospect_data["company_size"]
            if self.company_size_min <= size <= self.company_size_max:
                score += 1.0
            elif self.company_size_min <= size <= self.company_size_max * 1.5:
                score += 0.5
        
        # Geography match
        if self.geography and "location" in prospect_data:
            total_criteria += 1
            location = prospect_data["location"]
            if any(geo in location for geo in self.geography):
                score += 1.0
        
        # Job title match
        if self.job_titles and "title" in prospect_data:
            total_criteria += 1
            title = prospect_data["title"].lower()
            if any(job_title.lower() in title for job_title in self.job_titles):
                score += 1.0
        
        # Technology match
        if self.technologies and "technologies" in prospect_data:
            total_criteria += 1
            tech_matches = sum(
                1 for tech in self.technologies
                if tech in prospect_data["technologies"]
            )
            score += min(tech_matches / len(self.technologies), 1.0)
        
        # Keyword match
        if self.keywords:
            total_criteria += 1
            prospect_text = json.dumps(prospect_data).lower()
            keyword_matches = sum(
                1 for keyword in self.keywords
                if keyword.lower() in prospect_text
            )
            score += min(keyword_matches / len(self.keywords), 1.0)
        
        # Exclude keywords check
        if self.exclude_keywords:
            prospect_text = json.dumps(prospect_data).lower()
            if any(exclude.lower() in prospect_text for exclude in self.exclude_keywords):
                return False, 0.0
        
        if total_criteria == 0:
            return True, 0.5
        
        match_score = (score / total_criteria) * 100
        matches = match_score >= 50  # 50% match threshold
        
        return matches, match_score


class LeadGenerationAgent(BaseSalesAgent):
    """
    Agent specialized in finding and qualifying new leads.
    
    Features:
    - ICP-based prospect identification
    - Lead enrichment from multiple sources
    - Duplicate detection and merging
    - Lead scoring and prioritization
    - Automated outreach suggestions
    """
    
    def __init__(
        self,
        name: str = "LeadGenAgent",
        icp: Optional[IdealCustomerProfile] = None
    ):
        """
        Initialize lead generation agent.
        
        Args:
            name: Agent name
            icp: Ideal Customer Profile
        """
        prompts = Prompts(
            system="""You are a lead generation specialist focused on finding high-quality prospects.
            You identify potential customers, enrich their data, and prioritize them based on fit.
            You ensure data quality and prevent duplicates.""",
            
            reasoning_template="""Analyzing prospect for lead generation:
            Prospect Data: {prospect_data}
            ICP Match: {icp_match}
            Existing Leads: {existing_count}
            
            Evaluating fit and enrichment opportunities...""",
            
            action_template="""Lead Generation Result:
            Status: {status}
            Match Score: {match_score}
            Enrichment Added: {enrichments}
            Priority: {priority}
            Suggested Actions: {actions}"""
        )
        
        super().__init__(
            name=name,
            role="lead_generator",
            persona="Expert in prospect identification and enrichment",
            prompts=prompts
        )
        
        # ICP configuration
        self.icp = icp or IdealCustomerProfile()
        
        # Lead database (in production, this would be a real database)
        self.lead_database: Dict[str, Dict[str, Any]] = {}
        self.duplicate_keys: List[str] = ["email", "phone", "company_domain"]
        
        # Enrichment patterns
        self.enrichment_patterns = {
            "email_to_company": self._extract_company_from_email,
            "name_to_formal": self._formalize_name,
            "url_to_domain": self._extract_domain,
            "social_profiles": self._find_social_profiles
        }
        
        # Lead sources tracking
        self.source_performance: Dict[str, Dict[str, float]] = {}
    
    async def generate_leads(
        self,
        source_data: List[Dict[str, Any]],
        source: LeadSource = LeadSource.API
    ) -> Dict[str, Any]:
        """
        Generate leads from source data.
        
        Args:
            source_data: List of potential prospects
            source: Source of the leads
            
        Returns:
            Lead generation results
        """
        results = {
            "total_processed": len(source_data),
            "new_leads": [],
            "duplicates": [],
            "disqualified": [],
            "enriched": [],
            "statistics": {}
        }
        
        for prospect in source_data:
            # Check for duplicates
            duplicate_id = self._check_duplicate(prospect)
            if duplicate_id:
                results["duplicates"].append({
                    "prospect": prospect,
                    "existing_id": duplicate_id
                })
                continue
            
            # Enrich prospect data
            enriched = await self.enrich_prospect(prospect)
            
            # Check ICP match
            matches_icp, match_score = self.icp.matches(enriched)
            
            if not matches_icp:
                results["disqualified"].append({
                    "prospect": enriched,
                    "reason": "Does not match ICP",
                    "score": match_score
                })
                continue
            
            # Score and prioritize
            lead_score = self._calculate_lead_score(enriched, match_score)
            priority = self._determine_priority(lead_score)
            
            # Create lead record
            lead_id = self._generate_lead_id(enriched)
            lead_record = {
                "id": lead_id,
                "data": enriched,
                "source": source.value,
                "icp_score": match_score,
                "lead_score": lead_score,
                "priority": priority,
                "created_at": datetime.now().isoformat(),
                "status": "new",
                "assigned_to": None
            }
            
            # Store in database
            self.lead_database[lead_id] = lead_record
            results["new_leads"].append(lead_record)
            
            # Track source performance
            self._update_source_performance(source, lead_score)
        
        # Calculate statistics
        results["statistics"] = {
            "conversion_rate": len(results["new_leads"]) / len(source_data) if source_data else 0,
            "duplicate_rate": len(results["duplicates"]) / len(source_data) if source_data else 0,
            "avg_lead_score": sum(l["lead_score"] for l in results["new_leads"]) / len(results["new_leads"]) if results["new_leads"] else 0,
            "source_performance": self.source_performance.get(source.value, {})
        }
        
        # Update metrics
        self.metrics["leads_processed"] += len(source_data)
        self.metrics["qualified_leads"] += len(results["new_leads"])
        self.update_metrics("processed", results["statistics"]["avg_lead_score"])
        
        return results
    
    async def enrich_prospect(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich prospect data with additional information.
        
        Args:
            prospect_data: Basic prospect information
            
        Returns:
            Enriched prospect data
        """
        enriched = dict(prospect_data)
        
        # Apply enrichment patterns
        for pattern_name, pattern_func in self.enrichment_patterns.items():
            try:
                additional_data = pattern_func(enriched)
                enriched.update(additional_data)
            except Exception as e:
                # Log enrichment failure but continue
                pass
        
        # Company enrichment
        if "email" in enriched and "company" not in enriched:
            enriched["company"] = self._extract_company_from_email(enriched)["company"]
        
        # Title normalization
        if "title" in enriched:
            enriched["title_normalized"] = self._normalize_title(enriched["title"])
            enriched["seniority_level"] = self._determine_seniority(enriched["title"])
        
        # Contact information validation
        if "email" in enriched:
            enriched["email_valid"] = self._validate_email(enriched["email"])
        
        if "phone" in enriched:
            enriched["phone_formatted"] = self._format_phone(enriched["phone"])
        
        # Add enrichment metadata
        enriched["enriched_at"] = datetime.now().isoformat()
        enriched["enrichment_source"] = "internal"
        
        return enriched
    
    def _check_duplicate(self, prospect_data: Dict[str, Any]) -> Optional[str]:
        """Check if prospect is duplicate of existing lead."""
        for lead_id, lead in self.lead_database.items():
            for key in self.duplicate_keys:
                if key in prospect_data and key in lead["data"]:
                    if prospect_data[key] == lead["data"][key]:
                        return lead_id
        return None
    
    def _extract_company_from_email(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract company information from email domain."""
        if "email" not in data:
            return {}
        
        email = data["email"]
        domain = email.split("@")[-1]
        
        # Skip personal email domains
        personal_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
        if domain in personal_domains:
            return {"company_domain": domain, "is_corporate": False}
        
        # Extract company name from domain
        company_name = domain.split(".")[0]
        company_name = company_name.replace("-", " ").replace("_", " ").title()
        
        return {
            "company": company_name,
            "company_domain": domain,
            "is_corporate": True
        }
    
    def _formalize_name(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formalize name fields."""
        result = {}
        
        if "name" in data:
            parts = data["name"].split()
            if len(parts) >= 2:
                result["first_name"] = parts[0]
                result["last_name"] = " ".join(parts[1:])
            else:
                result["first_name"] = data["name"]
                result["last_name"] = ""
        
        return result
    
    def _extract_domain(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract domain from various URL fields."""
        result = {}
        
        for field in ["website", "url", "linkedin"]:
            if field in data:
                url = data[field]
                # Simple domain extraction
                domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', url)
                if domain_match:
                    result[f"{field}_domain"] = domain_match.group(1)
        
        return result
    
    def _find_social_profiles(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Find potential social media profiles."""
        profiles = {}
        
        # This would integrate with actual social media APIs
        # For now, return placeholder
        if "email" in data:
            username = data["email"].split("@")[0]
            profiles["social_profiles"] = {
                "linkedin": f"linkedin.com/in/{username}",
                "twitter": f"twitter.com/{username}"
            }
        
        return profiles
    
    def _normalize_title(self, title: str) -> str:
        """Normalize job title."""
        title_lower = title.lower()
        
        # Common normalizations
        normalizations = {
            "vp": "vice president",
            "sr": "senior",
            "jr": "junior",
            "mgr": "manager",
            "dir": "director",
            "eng": "engineer"
        }
        
        for abbrev, full in normalizations.items():
            title_lower = title_lower.replace(abbrev, full)
        
        return title_lower.title()
    
    def _determine_seniority(self, title: str) -> str:
        """Determine seniority level from title."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ["ceo", "cto", "cfo", "chief", "president"]):
            return "c_level"
        elif any(word in title_lower for word in ["vp", "vice president", "svp"]):
            return "vp_level"
        elif any(word in title_lower for word in ["director", "head"]):
            return "director_level"
        elif any(word in title_lower for word in ["manager", "lead"]):
            return "manager_level"
        elif any(word in title_lower for word in ["senior", "sr"]):
            return "senior_ic"
        else:
            return "individual_contributor"
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number."""
        # Remove non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Format as US phone number if 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone
    
    def _calculate_lead_score(self, prospect_data: Dict[str, Any], icp_score: float) -> float:
        """
        Calculate comprehensive lead score.
        
        Args:
            prospect_data: Enriched prospect data
            icp_score: ICP match score
            
        Returns:
            Lead score (0-100)
        """
        score = icp_score * 0.4  # ICP match is 40% of score
        
        # Data completeness (20%)
        required_fields = ["email", "company", "title", "phone"]
        completeness = sum(1 for f in required_fields if f in prospect_data) / len(required_fields)
        score += completeness * 20
        
        # Seniority (20%)
        seniority_scores = {
            "c_level": 20, "vp_level": 18, "director_level": 15,
            "manager_level": 10, "senior_ic": 5, "individual_contributor": 2
        }
        seniority = prospect_data.get("seniority_level", "individual_contributor")
        score += seniority_scores.get(seniority, 0)
        
        # Company size (10%)
        company_size = prospect_data.get("company_size", 0)
        if company_size > 1000:
            score += 10
        elif company_size > 100:
            score += 7
        elif company_size > 10:
            score += 4
        
        # Engagement indicators (10%)
        if prospect_data.get("requested_demo"):
            score += 10
        elif prospect_data.get("downloaded_content"):
            score += 5
        elif prospect_data.get("website_visit"):
            score += 2
        
        return min(score, 100.0)
    
    def _determine_priority(self, lead_score: float) -> str:
        """Determine lead priority based on score."""
        if lead_score >= 80:
            return "hot"
        elif lead_score >= 60:
            return "warm"
        elif lead_score >= 40:
            return "cool"
        else:
            return "cold"
    
    def _generate_lead_id(self, prospect_data: Dict[str, Any]) -> str:
        """Generate unique lead ID."""
        import hashlib
        
        # Create ID from email or company + name
        if "email" in prospect_data:
            base = prospect_data["email"]
        else:
            base = f"{prospect_data.get('company', '')}_{prospect_data.get('name', '')}"
        
        return hashlib.md5(base.encode()).hexdigest()[:12]
    
    def _update_source_performance(self, source: LeadSource, lead_score: float):
        """Update source performance metrics."""
        if source.value not in self.source_performance:
            self.source_performance[source.value] = {
                "count": 0,
                "total_score": 0,
                "avg_score": 0
            }
        
        perf = self.source_performance[source.value]
        perf["count"] += 1
        perf["total_score"] += lead_score
        perf["avg_score"] = perf["total_score"] / perf["count"]
    
    def get_leads_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """Get leads filtered by priority."""
        return [
            lead for lead in self.lead_database.values()
            if lead["priority"] == priority
        ]
    
    def get_lead_summary(self) -> Dict[str, Any]:
        """Get summary of lead generation performance."""
        total_leads = len(self.lead_database)
        
        if total_leads == 0:
            return {"message": "No leads generated yet"}
        
        priorities = {}
        for lead in self.lead_database.values():
            priority = lead["priority"]
            if priority not in priorities:
                priorities[priority] = 0
            priorities[priority] += 1
        
        return {
            "total_leads": total_leads,
            "by_priority": priorities,
            "avg_lead_score": sum(l["lead_score"] for l in self.lead_database.values()) / total_leads,
            "avg_icp_score": sum(l["icp_score"] for l in self.lead_database.values()) / total_leads,
            "source_performance": self.source_performance,
            "agent_metrics": self.metrics
        }
    
    def export_leads(self, format: str = "csv") -> str:
        """Export leads in specified format."""
        if format == "csv":
            lines = ["ID,Email,Company,Title,Score,Priority,Source,Created"]
            for lead in self.lead_database.values():
                data = lead["data"]
                lines.append(
                    f"{lead['id']},{data.get('email','')},{data.get('company','')},"
                    f"{data.get('title','')},{lead['lead_score']},{lead['priority']},"
                    f"{lead['source']},{lead['created_at']}"
                )
            return "\n".join(lines)
        else:
            return json.dumps(list(self.lead_database.values()), indent=2)