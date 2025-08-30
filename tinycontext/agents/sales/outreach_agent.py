"""
Outreach Agent for TinyContext.

Handles personalized communication and follow-ups.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from .base_sales_agent import BaseSalesAgent
from ..loader import Prompts


class OutreachType(Enum):
    """Types of outreach."""
    COLD_EMAIL = "cold_email"
    FOLLOW_UP = "follow_up"
    NURTURE = "nurture"
    RE_ENGAGEMENT = "re_engagement"
    DEMO_REQUEST = "demo_request"
    PROPOSAL = "proposal"
    THANK_YOU = "thank_you"


@dataclass
class OutreachTemplate:
    """Template for outreach messages."""
    name: str
    type: OutreachType
    subject_template: str
    body_template: str
    variables: List[str]
    follow_up_sequence: List[Dict[str, Any]] = field(default_factory=list)
    personalization_fields: List[str] = field(default_factory=list)
    
    def render(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Render template with data."""
        subject = self.subject_template
        body = self.body_template
        
        for var in self.variables:
            value = data.get(var, f"[{var}]")
            subject = subject.replace(f"{{{var}}}", str(value))
            body = body.replace(f"{{{var}}}", str(value))
        
        return {
            "subject": subject,
            "body": body
        }


@dataclass
class OutreachCampaign:
    """Outreach campaign configuration."""
    name: str
    target_audience: str
    templates: List[OutreachTemplate]
    schedule: Dict[str, Any]
    metrics: Dict[str, int] = field(default_factory=lambda: {
        "sent": 0, "opened": 0, "replied": 0, "clicked": 0, "converted": 0
    })


class OutreachAgent(BaseSalesAgent):
    """
    Agent specialized in personalized outreach and communication.
    
    Features:
    - Template-based messaging
    - Personalization engine
    - Follow-up sequences
    - A/B testing
    - Response tracking
    """
    
    def __init__(self, name: str = "OutreachAgent"):
        """Initialize outreach agent."""
        prompts = Prompts(
            system="""You are an outreach specialist who creates personalized, engaging communications.
            You understand how to craft messages that resonate with prospects and drive responses.
            You follow best practices for email deliverability and engagement.""",
            
            reasoning_template="""Creating personalized outreach:
            Recipient: {recipient}
            Context: {context}
            Goal: {goal}
            Previous Interactions: {history}
            
            Crafting personalized message...""",
            
            action_template="""Outreach Created:
            Type: {outreach_type}
            Subject: {subject}
            Personalization Score: {personalization_score}
            Estimated Response Rate: {response_rate}
            Follow-up Schedule: {follow_ups}"""
        )
        
        super().__init__(
            name=name,
            role="outreach_specialist",
            persona="Expert in personalized communication and engagement",
            prompts=prompts
        )
        
        # Initialize templates
        self.templates = self._initialize_templates()
        
        # Campaigns
        self.campaigns: Dict[str, OutreachCampaign] = {}
        
        # Personalization engine
        self.personalization_rules = self._initialize_personalization_rules()
        
        # Response tracking
        self.outreach_history: List[Dict[str, Any]] = []
    
    def _initialize_templates(self) -> Dict[str, OutreachTemplate]:
        """Initialize outreach templates."""
        templates = {}
        
        # Cold email template
        templates["cold_email"] = OutreachTemplate(
            name="Cold Email",
            type=OutreachType.COLD_EMAIL,
            subject_template="Quick question about {company}'s {pain_point}",
            body_template="""Hi {first_name},

I noticed that {company} is {company_context}. Many companies in {industry} struggle with {pain_point}.

We've helped similar companies {value_proposition}, resulting in {expected_outcome}.

Would you be open to a brief 15-minute call to discuss how this might apply to {company}?

Best regards,
{sender_name}""",
            variables=["first_name", "company", "company_context", "industry", 
                      "pain_point", "value_proposition", "expected_outcome", "sender_name"],
            follow_up_sequence=[
                {"days": 3, "template": "cold_email_followup_1"},
                {"days": 7, "template": "cold_email_followup_2"},
                {"days": 14, "template": "cold_email_followup_3"}
            ]
        )
        
        # Follow-up template
        templates["follow_up"] = OutreachTemplate(
            name="Follow Up",
            type=OutreachType.FOLLOW_UP,
            subject_template="Re: {original_subject}",
            body_template="""Hi {first_name},

I wanted to follow up on my previous email about {topic}.

{follow_up_hook}

I understand you're busy, so I'll keep this brief. {value_reminder}

Are you available for a quick call this week? I have some time on {availability}.

Thanks,
{sender_name}""",
            variables=["first_name", "original_subject", "topic", "follow_up_hook",
                      "value_reminder", "availability", "sender_name"]
        )
        
        # Demo request template
        templates["demo_request"] = OutreachTemplate(
            name="Demo Request Follow-up",
            type=OutreachType.DEMO_REQUEST,
            subject_template="Your demo request - {company} + {product_name}",
            body_template="""Hi {first_name},

Thank you for requesting a demo of {product_name}!

Based on what you told us about {use_case}, I've prepared a personalized demo that will show you exactly how we can help {company} {key_benefit}.

Here are a few times that work for me:
{time_slots}

The demo will take about 30 minutes, and we'll cover:
- {demo_point_1}
- {demo_point_2}
- {demo_point_3}

Which time works best for you?

Looking forward to speaking with you!

Best,
{sender_name}""",
            variables=["first_name", "company", "product_name", "use_case",
                      "key_benefit", "time_slots", "demo_point_1", "demo_point_2",
                      "demo_point_3", "sender_name"]
        )
        
        # Nurture template
        templates["nurture"] = OutreachTemplate(
            name="Nurture Email",
            type=OutreachType.NURTURE,
            subject_template="{resource_type}: {resource_title}",
            body_template="""Hi {first_name},

I thought you might find this {resource_type} interesting given your role at {company}.

{resource_description}

{resource_link}

Key takeaways:
• {takeaway_1}
• {takeaway_2}
• {takeaway_3}

Let me know if you'd like to discuss how these insights could apply to {company}'s {challenge}.

Best,
{sender_name}""",
            variables=["first_name", "company", "resource_type", "resource_title",
                      "resource_description", "resource_link", "takeaway_1",
                      "takeaway_2", "takeaway_3", "challenge", "sender_name"]
        )
        
        return templates
    
    def _initialize_personalization_rules(self) -> Dict[str, Any]:
        """Initialize personalization rules."""
        return {
            "industry_specific": {
                "technology": ["scale", "innovation", "efficiency"],
                "healthcare": ["compliance", "patient care", "efficiency"],
                "finance": ["compliance", "risk", "automation"],
                "retail": ["customer experience", "inventory", "omnichannel"]
            },
            "role_specific": {
                "executive": ["strategic", "ROI", "competitive advantage"],
                "manager": ["team productivity", "processes", "metrics"],
                "individual": ["ease of use", "time-saving", "daily tasks"]
            },
            "company_size": {
                "enterprise": ["scale", "integration", "compliance"],
                "mid_market": ["growth", "efficiency", "flexibility"],
                "small": ["cost-effective", "easy setup", "support"]
            }
        }
    
    async def create_outreach(
        self,
        recipient: Dict[str, Any],
        outreach_type: OutreachType,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create personalized outreach for a recipient.
        
        Args:
            recipient: Recipient information
            outreach_type: Type of outreach
            context: Additional context
            
        Returns:
            Outreach message and metadata
        """
        # Select template
        template = self._select_template(outreach_type)
        
        # Enrich recipient data
        enriched_recipient = self._enrich_recipient_data(recipient)
        
        # Generate personalization data
        personalization_data = self._generate_personalization(enriched_recipient, context)
        
        # Render template
        message = template.render(personalization_data)
        
        # Calculate personalization score
        personalization_score = self._calculate_personalization_score(message, personalization_data)
        
        # Estimate response rate
        response_rate = self._estimate_response_rate(outreach_type, personalization_score)
        
        # Create follow-up schedule
        follow_ups = self._create_follow_up_schedule(template, recipient)
        
        # Record outreach
        outreach_record = {
            "id": f"outreach_{datetime.now().timestamp()}",
            "recipient": enriched_recipient,
            "type": outreach_type.value,
            "message": message,
            "personalization_score": personalization_score,
            "estimated_response_rate": response_rate,
            "follow_ups": follow_ups,
            "created_at": datetime.now().isoformat(),
            "status": "draft"
        }
        
        self.outreach_history.append(outreach_record)
        
        # Update metrics
        self.metrics["leads_processed"] += 1
        
        return outreach_record
    
    def _select_template(self, outreach_type: OutreachType) -> OutreachTemplate:
        """Select appropriate template."""
        for template in self.templates.values():
            if template.type == outreach_type:
                return template
        
        # Default to cold email if not found
        return self.templates["cold_email"]
    
    def _enrich_recipient_data(self, recipient: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich recipient data for personalization."""
        enriched = dict(recipient)
        
        # Add derived fields
        if "email" in recipient:
            domain = recipient["email"].split("@")[-1]
            enriched["company_domain"] = domain
            if "company" not in enriched:
                enriched["company"] = domain.split(".")[0].title()
        
        # Add industry if not present
        if "industry" not in enriched:
            enriched["industry"] = self._infer_industry(enriched)
        
        # Add seniority level
        if "title" in enriched:
            enriched["seniority"] = self._determine_seniority(enriched["title"])
        
        return enriched
    
    def _generate_personalization(
        self,
        recipient: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate personalization data."""
        data = dict(recipient)
        
        # Add context data
        if context:
            data.update(context)
        
        # Add industry-specific value props
        industry = recipient.get("industry", "").lower()
        if industry in self.personalization_rules["industry_specific"]:
            data["pain_point"] = self.personalization_rules["industry_specific"][industry][0]
            data["value_proposition"] = f"improve {self.personalization_rules['industry_specific'][industry][1]}"
        
        # Add role-specific messaging
        seniority = recipient.get("seniority", "individual")
        if seniority in self.personalization_rules["role_specific"]:
            data["key_benefit"] = self.personalization_rules["role_specific"][seniority][0]
        
        # Add default values for missing fields
        defaults = {
            "first_name": recipient.get("name", "there"),
            "company": recipient.get("company", "your company"),
            "industry": recipient.get("industry", "your industry"),
            "sender_name": "Sales Team",
            "product_name": "our solution",
            "availability": "Tuesday or Thursday afternoon",
            "follow_up_hook": "I wanted to make sure this didn't get buried in your inbox.",
            "value_reminder": "We can typically help companies like yours save 20% on operational costs.",
            "expected_outcome": "20-30% improvement in efficiency"
        }
        
        for key, value in defaults.items():
            if key not in data:
                data[key] = value
        
        return data
    
    def _calculate_personalization_score(
        self,
        message: Dict[str, str],
        personalization_data: Dict[str, Any]
    ) -> float:
        """Calculate how personalized the message is."""
        score = 0.0
        
        # Check for personalized fields
        personalized_fields = ["first_name", "company", "industry", "title", "pain_point"]
        fields_used = sum(
            1 for field in personalized_fields
            if field in personalization_data and
            personalization_data[field] not in ["there", "your company", "your industry"]
        )
        score += (fields_used / len(personalized_fields)) * 50
        
        # Check for specific details
        if "company_context" in personalization_data:
            score += 20
        
        # Check for relevant use case
        if "use_case" in personalization_data:
            score += 15
        
        # Check for timely reference
        if "recent_event" in personalization_data or "recent_news" in personalization_data:
            score += 15
        
        return min(score, 100.0)
    
    def _estimate_response_rate(
        self,
        outreach_type: OutreachType,
        personalization_score: float
    ) -> float:
        """Estimate response rate based on type and personalization."""
        # Base rates by type
        base_rates = {
            OutreachType.COLD_EMAIL: 2.0,
            OutreachType.FOLLOW_UP: 8.0,
            OutreachType.NURTURE: 5.0,
            OutreachType.RE_ENGAGEMENT: 3.0,
            OutreachType.DEMO_REQUEST: 40.0,
            OutreachType.PROPOSAL: 25.0,
            OutreachType.THANK_YOU: 15.0
        }
        
        base_rate = base_rates.get(outreach_type, 5.0)
        
        # Adjust based on personalization
        multiplier = 1.0 + (personalization_score / 100.0)
        
        return min(base_rate * multiplier, 50.0)
    
    def _create_follow_up_schedule(
        self,
        template: OutreachTemplate,
        recipient: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create follow-up schedule."""
        schedule = []
        
        for follow_up in template.follow_up_sequence:
            schedule.append({
                "send_date": (datetime.now() + timedelta(days=follow_up["days"])).isoformat(),
                "template": follow_up["template"],
                "recipient": recipient.get("email", ""),
                "status": "scheduled"
            })
        
        return schedule
    
    def _infer_industry(self, data: Dict[str, Any]) -> str:
        """Infer industry from available data."""
        # Simple inference based on domain or company name
        company = data.get("company", "").lower()
        domain = data.get("company_domain", "").lower()
        
        tech_indicators = ["tech", "software", "cloud", "data", "ai", "ml"]
        healthcare_indicators = ["health", "medical", "pharma", "bio"]
        finance_indicators = ["bank", "finance", "capital", "invest"]
        
        combined = f"{company} {domain}"
        
        if any(ind in combined for ind in tech_indicators):
            return "technology"
        elif any(ind in combined for ind in healthcare_indicators):
            return "healthcare"
        elif any(ind in combined for ind in finance_indicators):
            return "finance"
        else:
            return "general"
    
    def _determine_seniority(self, title: str) -> str:
        """Determine seniority from title."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ["ceo", "cto", "cfo", "chief", "president"]):
            return "c_level"
        elif any(word in title_lower for word in ["vp", "vice president", "director"]):
            return "executive"
        elif any(word in title_lower for word in ["manager", "lead", "head"]):
            return "manager"
        else:
            return "individual"
    
    async def create_campaign(
        self,
        name: str,
        recipients: List[Dict[str, Any]],
        outreach_type: OutreachType,
        schedule: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an outreach campaign.
        
        Args:
            name: Campaign name
            recipients: List of recipients
            outreach_type: Type of outreach
            schedule: Scheduling configuration
            
        Returns:
            Campaign details
        """
        # Create campaign
        campaign = OutreachCampaign(
            name=name,
            target_audience=f"{len(recipients)} recipients",
            templates=[self._select_template(outreach_type)],
            schedule=schedule or {"immediate": True}
        )
        
        # Generate outreach for each recipient
        outreach_messages = []
        for recipient in recipients:
            message = await self.create_outreach(recipient, outreach_type)
            outreach_messages.append(message)
        
        # Store campaign
        self.campaigns[name] = campaign
        
        return {
            "campaign_name": name,
            "recipients_count": len(recipients),
            "messages_created": len(outreach_messages),
            "avg_personalization_score": sum(m["personalization_score"] for m in outreach_messages) / len(outreach_messages),
            "estimated_responses": sum(m["estimated_response_rate"] for m in outreach_messages) / 100 * len(outreach_messages),
            "schedule": schedule
        }
    
    def track_response(self, outreach_id: str, response_type: str):
        """
        Track response to outreach.
        
        Args:
            outreach_id: Outreach ID
            response_type: Type of response (opened, clicked, replied, etc.)
        """
        for outreach in self.outreach_history:
            if outreach["id"] == outreach_id:
                if "responses" not in outreach:
                    outreach["responses"] = []
                
                outreach["responses"].append({
                    "type": response_type,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Update campaign metrics if part of one
                for campaign in self.campaigns.values():
                    if response_type in campaign.metrics:
                        campaign.metrics[response_type] += 1
                
                break
    
    def get_campaign_performance(self, campaign_name: str) -> Dict[str, Any]:
        """Get performance metrics for a campaign."""
        if campaign_name not in self.campaigns:
            return {"error": "Campaign not found"}
        
        campaign = self.campaigns[campaign_name]
        
        # Calculate rates
        metrics = campaign.metrics.copy()
        if metrics["sent"] > 0:
            metrics["open_rate"] = (metrics["opened"] / metrics["sent"]) * 100
            metrics["reply_rate"] = (metrics["replied"] / metrics["sent"]) * 100
            metrics["click_rate"] = (metrics["clicked"] / metrics["sent"]) * 100
            metrics["conversion_rate"] = (metrics["converted"] / metrics["sent"]) * 100
        
        return {
            "campaign": campaign_name,
            "metrics": metrics,
            "target_audience": campaign.target_audience,
            "templates_used": [t.name for t in campaign.templates]
        }
    
    def optimize_template(self, template_name: str, performance_data: Dict[str, float]):
        """
        Optimize template based on performance data.
        
        Args:
            template_name: Template to optimize
            performance_data: Performance metrics
        """
        if template_name not in self.templates:
            return
        
        template = self.templates[template_name]
        
        # Simple optimization: adjust follow-up timing based on response rates
        if "response_rate" in performance_data:
            if performance_data["response_rate"] < 5:
                # Poor performance - adjust follow-up timing
                for follow_up in template.follow_up_sequence:
                    follow_up["days"] = max(follow_up["days"] - 1, 1)
            elif performance_data["response_rate"] > 20:
                # Good performance - can space out follow-ups
                for follow_up in template.follow_up_sequence:
                    follow_up["days"] = follow_up["days"] + 1