"""
Integration Discovery Agent for TinyContext.

Analyzes requirements and discovers necessary integrations.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re

from .base_sales_agent import BaseSalesAgent
from ..loader import Prompts


class IntegrationType(Enum):
    """Types of integrations."""
    CRM = "crm"
    DATABASE = "database"
    EMAIL = "email"
    ANALYTICS = "analytics"
    PAYMENT = "payment"
    COMMUNICATION = "communication"
    MARKETING = "marketing"
    SUPPORT = "support"
    API = "api"
    WEBHOOK = "webhook"
    FILE_STORAGE = "file_storage"
    CALENDAR = "calendar"


@dataclass
class Integration:
    """Integration definition."""
    name: str
    type: IntegrationType
    provider: str
    capabilities: List[str]
    required_credentials: List[str]
    api_endpoints: Dict[str, str] = field(default_factory=dict)
    data_schema: Dict[str, Any] = field(default_factory=dict)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    documentation_url: str = ""
    setup_complexity: str = "medium"  # low, medium, high
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "provider": self.provider,
            "capabilities": self.capabilities,
            "required_credentials": self.required_credentials,
            "api_endpoints": self.api_endpoints,
            "data_schema": self.data_schema,
            "rate_limits": self.rate_limits,
            "documentation_url": self.documentation_url,
            "setup_complexity": self.setup_complexity
        }


@dataclass
class IntegrationRequirement:
    """Requirement for an integration."""
    description: str
    required_operations: List[str]
    data_types: List[str]
    frequency: str  # realtime, hourly, daily, weekly
    volume: str  # low, medium, high
    priority: str  # critical, high, medium, low
    
    def matches_integration(self, integration: Integration) -> float:
        """Calculate match score for an integration."""
        score = 0.0
        
        # Check operation coverage
        ops_covered = sum(
            1 for op in self.required_operations
            if any(cap in integration.capabilities for cap in [op, f"can_{op}"])
        )
        if self.required_operations:
            score += (ops_covered / len(self.required_operations)) * 50
        
        # Check data type support
        data_supported = sum(
            1 for dt in self.data_types
            if dt in str(integration.data_schema)
        )
        if self.data_types:
            score += (data_supported / len(self.data_types)) * 30
        
        # Complexity penalty
        complexity_scores = {"low": 20, "medium": 15, "high": 5}
        score += complexity_scores.get(integration.setup_complexity, 10)
        
        return min(score, 100.0)


class IntegrationDiscoveryAgent(BaseSalesAgent):
    """
    Agent specialized in discovering and recommending integrations.
    
    Features:
    - Natural language requirement analysis
    - Integration catalog search
    - Compatibility checking
    - Setup guide generation
    - Connection testing
    """
    
    def __init__(self, name: str = "IntegrationDiscoveryAgent"):
        """Initialize integration discovery agent."""
        prompts = Prompts(
            system="""You are an integration specialist who analyzes requirements and recommends appropriate integrations.
            You understand various APIs, databases, and third-party services.
            You can identify integration needs from natural language descriptions.""",
            
            reasoning_template="""Analyzing integration requirements:
            Description: {description}
            Detected Operations: {operations}
            Data Types: {data_types}
            Available Integrations: {available_count}
            
            Matching integrations to requirements...""",
            
            action_template="""Integration Discovery Result:
            Recommended Integrations: {recommendations}
            Required Setup: {setup_steps}
            Estimated Complexity: {complexity}
            Missing Capabilities: {gaps}"""
        )
        
        super().__init__(
            name=name,
            role="integration_specialist",
            persona="Expert in system integrations and API connections",
            prompts=prompts
        )
        
        # Integration catalog
        self.catalog = self._initialize_catalog()
        
        # Pattern matching for requirement extraction
        self.operation_patterns = {
            "create": ["create", "add", "insert", "new"],
            "read": ["read", "get", "fetch", "retrieve", "find", "search"],
            "update": ["update", "modify", "change", "edit"],
            "delete": ["delete", "remove", "destroy"],
            "sync": ["sync", "synchronize", "replicate", "mirror"],
            "import": ["import", "load", "ingest"],
            "export": ["export", "extract", "download"],
            "send": ["send", "email", "notify", "message"],
            "connect": ["connect", "link", "integrate"]
        }
        
        # Data type patterns
        self.data_type_patterns = {
            "contact": ["contact", "lead", "prospect", "customer"],
            "company": ["company", "account", "organization"],
            "deal": ["deal", "opportunity", "sale"],
            "email": ["email", "message", "correspondence"],
            "event": ["event", "meeting", "appointment", "call"],
            "task": ["task", "todo", "activity"],
            "document": ["document", "file", "attachment"],
            "invoice": ["invoice", "billing", "payment"]
        }
    
    def _initialize_catalog(self) -> Dict[str, Integration]:
        """Initialize integration catalog with common integrations."""
        catalog = {}
        
        # Salesforce
        catalog["salesforce"] = Integration(
            name="Salesforce",
            type=IntegrationType.CRM,
            provider="Salesforce",
            capabilities=["create", "read", "update", "delete", "sync", "bulk_operations"],
            required_credentials=["client_id", "client_secret", "username", "password", "security_token"],
            api_endpoints={
                "auth": "https://login.salesforce.com/services/oauth2/token",
                "rest": "/services/data/v58.0/",
                "bulk": "/services/data/v58.0/jobs/ingest"
            },
            documentation_url="https://developer.salesforce.com/docs/apis",
            setup_complexity="high"
        )
        
        # HubSpot
        catalog["hubspot"] = Integration(
            name="HubSpot",
            type=IntegrationType.CRM,
            provider="HubSpot",
            capabilities=["create", "read", "update", "delete", "sync", "webhooks"],
            required_credentials=["api_key"],
            api_endpoints={
                "contacts": "https://api.hubapi.com/crm/v3/objects/contacts",
                "companies": "https://api.hubapi.com/crm/v3/objects/companies",
                "deals": "https://api.hubapi.com/crm/v3/objects/deals"
            },
            rate_limits={"requests_per_second": 10, "requests_per_day": 250000},
            documentation_url="https://developers.hubspot.com/docs/api",
            setup_complexity="low"
        )
        
        # PostgreSQL
        catalog["postgresql"] = Integration(
            name="PostgreSQL",
            type=IntegrationType.DATABASE,
            provider="PostgreSQL",
            capabilities=["create", "read", "update", "delete", "transactions", "bulk_operations"],
            required_credentials=["host", "port", "database", "username", "password"],
            data_schema={"supports": ["relational", "json", "arrays"]},
            documentation_url="https://www.postgresql.org/docs/",
            setup_complexity="medium"
        )
        
        # MongoDB
        catalog["mongodb"] = Integration(
            name="MongoDB",
            type=IntegrationType.DATABASE,
            provider="MongoDB",
            capabilities=["create", "read", "update", "delete", "aggregation", "real_time"],
            required_credentials=["connection_string"],
            data_schema={"supports": ["document", "json", "binary"]},
            documentation_url="https://docs.mongodb.com/",
            setup_complexity="medium"
        )
        
        # SendGrid
        catalog["sendgrid"] = Integration(
            name="SendGrid",
            type=IntegrationType.EMAIL,
            provider="SendGrid",
            capabilities=["send_email", "templates", "tracking", "webhooks"],
            required_credentials=["api_key"],
            api_endpoints={
                "send": "https://api.sendgrid.com/v3/mail/send",
                "templates": "https://api.sendgrid.com/v3/templates"
            },
            rate_limits={"emails_per_day": 100},
            documentation_url="https://sendgrid.com/docs/api-reference/",
            setup_complexity="low"
        )
        
        # Slack
        catalog["slack"] = Integration(
            name="Slack",
            type=IntegrationType.COMMUNICATION,
            provider="Slack",
            capabilities=["send_message", "create_channel", "webhooks", "slash_commands"],
            required_credentials=["bot_token", "webhook_url"],
            api_endpoints={
                "post_message": "https://slack.com/api/chat.postMessage",
                "webhook": "https://hooks.slack.com/services/"
            },
            documentation_url="https://api.slack.com/",
            setup_complexity="low"
        )
        
        # Stripe
        catalog["stripe"] = Integration(
            name="Stripe",
            type=IntegrationType.PAYMENT,
            provider="Stripe",
            capabilities=["process_payment", "subscriptions", "invoicing", "webhooks"],
            required_credentials=["secret_key", "publishable_key"],
            api_endpoints={
                "charges": "https://api.stripe.com/v1/charges",
                "customers": "https://api.stripe.com/v1/customers"
            },
            documentation_url="https://stripe.com/docs/api",
            setup_complexity="medium"
        )
        
        # Google Calendar
        catalog["google_calendar"] = Integration(
            name="Google Calendar",
            type=IntegrationType.CALENDAR,
            provider="Google",
            capabilities=["create_event", "read_calendar", "update_event", "reminders"],
            required_credentials=["client_id", "client_secret", "refresh_token"],
            api_endpoints={
                "events": "https://www.googleapis.com/calendar/v3/calendars/",
            },
            documentation_url="https://developers.google.com/calendar/api",
            setup_complexity="medium"
        )
        
        return catalog
    
    async def analyze_requirements(self, description: str) -> Dict[str, Any]:
        """
        Analyze natural language requirements for integrations.
        
        Args:
            description: Natural language description of needs
            
        Returns:
            Analysis results with recommendations
        """
        # Extract operations
        operations = self._extract_operations(description)
        
        # Extract data types
        data_types = self._extract_data_types(description)
        
        # Identify integration types needed
        integration_types = self._identify_integration_types(description)
        
        # Create requirement
        requirement = IntegrationRequirement(
            description=description,
            required_operations=operations,
            data_types=data_types,
            frequency=self._extract_frequency(description),
            volume=self._extract_volume(description),
            priority="high"
        )
        
        # Find matching integrations
        recommendations = self._find_matching_integrations(requirement)
        
        # Identify gaps
        gaps = self._identify_capability_gaps(requirement, recommendations)
        
        # Generate setup guide
        setup_guide = self._generate_setup_guide(recommendations)
        
        result = {
            "analysis": {
                "description": description,
                "detected_operations": operations,
                "detected_data_types": data_types,
                "integration_types": [t.value for t in integration_types],
                "frequency": requirement.frequency,
                "volume": requirement.volume
            },
            "recommendations": recommendations,
            "setup_guide": setup_guide,
            "capability_gaps": gaps,
            "estimated_complexity": self._estimate_overall_complexity(recommendations)
        }
        
        # Update context
        self.sales_context.metadata["last_analysis"] = result
        self.sales_context.integrations_available = [r["name"] for r in recommendations]
        
        return result
    
    def _extract_operations(self, text: str) -> List[str]:
        """Extract operations from text."""
        text_lower = text.lower()
        operations = []
        
        for operation, keywords in self.operation_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                operations.append(operation)
        
        return operations
    
    def _extract_data_types(self, text: str) -> List[str]:
        """Extract data types from text."""
        text_lower = text.lower()
        data_types = []
        
        for data_type, keywords in self.data_type_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                data_types.append(data_type)
        
        return data_types
    
    def _identify_integration_types(self, text: str) -> List[IntegrationType]:
        """Identify types of integrations needed."""
        text_lower = text.lower()
        types = []
        
        # CRM indicators
        if any(word in text_lower for word in ["crm", "salesforce", "hubspot", "customer relationship"]):
            types.append(IntegrationType.CRM)
        
        # Database indicators
        if any(word in text_lower for word in ["database", "sql", "mongodb", "store data", "data storage"]):
            types.append(IntegrationType.DATABASE)
        
        # Email indicators
        if any(word in text_lower for word in ["email", "send messages", "notifications"]):
            types.append(IntegrationType.EMAIL)
        
        # Communication indicators
        if any(word in text_lower for word in ["slack", "teams", "chat", "messaging"]):
            types.append(IntegrationType.COMMUNICATION)
        
        # Payment indicators
        if any(word in text_lower for word in ["payment", "billing", "invoice", "stripe"]):
            types.append(IntegrationType.PAYMENT)
        
        # Calendar indicators
        if any(word in text_lower for word in ["calendar", "schedule", "meeting", "appointment"]):
            types.append(IntegrationType.CALENDAR)
        
        # Default to API if no specific type identified
        if not types:
            types.append(IntegrationType.API)
        
        return types
    
    def _extract_frequency(self, text: str) -> str:
        """Extract frequency requirement from text."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["real-time", "realtime", "instant", "immediately"]):
            return "realtime"
        elif any(word in text_lower for word in ["hourly", "every hour"]):
            return "hourly"
        elif any(word in text_lower for word in ["daily", "every day", "each day"]):
            return "daily"
        elif any(word in text_lower for word in ["weekly", "every week"]):
            return "weekly"
        else:
            return "daily"  # default
    
    def _extract_volume(self, text: str) -> str:
        """Extract volume requirement from text."""
        text_lower = text.lower()
        
        # Look for numeric indicators
        numbers = re.findall(r'\d+', text)
        if numbers:
            max_num = max(int(n) for n in numbers)
            if max_num > 10000:
                return "high"
            elif max_num > 100:
                return "medium"
        
        # Look for volume keywords
        if any(word in text_lower for word in ["bulk", "large", "massive", "thousands"]):
            return "high"
        elif any(word in text_lower for word in ["moderate", "hundreds"]):
            return "medium"
        else:
            return "low"
    
    def _find_matching_integrations(self, requirement: IntegrationRequirement) -> List[Dict[str, Any]]:
        """Find integrations matching the requirement."""
        matches = []
        
        for name, integration in self.catalog.items():
            score = requirement.matches_integration(integration)
            if score > 30:  # Minimum threshold
                matches.append({
                    "name": integration.name,
                    "type": integration.type.value,
                    "provider": integration.provider,
                    "match_score": score,
                    "capabilities": integration.capabilities,
                    "setup_complexity": integration.setup_complexity,
                    "documentation": integration.documentation_url
                })
        
        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        return matches[:5]  # Return top 5 matches
    
    def _identify_capability_gaps(
        self,
        requirement: IntegrationRequirement,
        recommendations: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify capabilities not covered by recommendations."""
        gaps = []
        
        # Get all capabilities from recommendations
        covered_operations = set()
        for rec in recommendations:
            covered_operations.update(rec["capabilities"])
        
        # Find gaps
        for op in requirement.required_operations:
            if op not in covered_operations and f"can_{op}" not in covered_operations:
                gaps.append(f"Operation '{op}' not fully covered")
        
        return gaps
    
    def _generate_setup_guide(self, recommendations: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Generate setup guide for recommended integrations."""
        guide = {}
        
        for rec in recommendations:
            name = rec["name"]
            integration = self.catalog.get(name.lower().replace(" ", "_"))
            
            if not integration:
                continue
            
            steps = []
            
            # Authentication setup
            if integration.required_credentials:
                steps.append(f"Obtain credentials: {', '.join(integration.required_credentials)}")
            
            # API setup
            if integration.api_endpoints:
                steps.append("Configure API endpoints")
            
            # Testing
            steps.append("Test connection with sample data")
            
            # Data mapping
            if integration.data_schema:
                steps.append("Map data fields to integration schema")
            
            # Rate limit configuration
            if integration.rate_limits:
                limits = ", ".join(f"{k}: {v}" for k, v in integration.rate_limits.items())
                steps.append(f"Configure rate limiting ({limits})")
            
            # Documentation
            if integration.documentation_url:
                steps.append(f"Review documentation: {integration.documentation_url}")
            
            guide[name] = steps
        
        return guide
    
    def _estimate_overall_complexity(self, recommendations: List[Dict[str, Any]]) -> str:
        """Estimate overall setup complexity."""
        if not recommendations:
            return "none"
        
        complexities = [rec["setup_complexity"] for rec in recommendations]
        
        if "high" in complexities:
            return "high"
        elif "medium" in complexities:
            return "medium"
        else:
            return "low"
    
    async def test_connection(self, integration_name: str, credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Test connection to an integration.
        
        Args:
            integration_name: Name of integration
            credentials: Credentials for connection
            
        Returns:
            Connection test results
        """
        integration = self.catalog.get(integration_name.lower().replace(" ", "_"))
        
        if not integration:
            return {
                "success": False,
                "error": f"Integration '{integration_name}' not found in catalog"
            }
        
        # Check required credentials
        missing = [cred for cred in integration.required_credentials if cred not in credentials]
        if missing:
            return {
                "success": False,
                "error": f"Missing required credentials: {', '.join(missing)}"
            }
        
        # Simulate connection test (in production, would actually test)
        return {
            "success": True,
            "integration": integration_name,
            "capabilities_available": integration.capabilities,
            "rate_limits": integration.rate_limits,
            "message": "Connection successful"
        }
    
    def get_integration_details(self, integration_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an integration."""
        integration = self.catalog.get(integration_name.lower().replace(" ", "_"))
        
        if not integration:
            return None
        
        return integration.to_dict()
    
    def add_custom_integration(self, integration: Integration):
        """Add a custom integration to the catalog."""
        key = integration.name.lower().replace(" ", "_")
        self.catalog[key] = integration
    
    def generate_connection_code(self, integration_name: str, language: str = "python") -> str:
        """
        Generate sample connection code for an integration.
        
        Args:
            integration_name: Name of integration
            language: Programming language
            
        Returns:
            Sample code
        """
        integration = self.catalog.get(integration_name.lower().replace(" ", "_"))
        
        if not integration:
            return "# Integration not found"
        
        if language == "python":
            if integration.type == IntegrationType.DATABASE:
                if "postgresql" in integration_name.lower():
                    return """import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="your_host",
    port=5432,
    database="your_database",
    user="your_username",
    password="your_password"
)

# Create cursor
cur = conn.cursor()

# Execute query
cur.execute("SELECT * FROM leads LIMIT 10")
results = cur.fetchall()

# Close connection
cur.close()
conn.close()"""
                elif "mongodb" in integration_name.lower():
                    return """from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://username:password@host:port/')
db = client['your_database']
collection = db['leads']

# Find documents
results = collection.find().limit(10)

# Close connection
client.close()"""
            
            elif integration.type == IntegrationType.CRM:
                if "hubspot" in integration_name.lower():
                    return """import requests

API_KEY = 'your_api_key'
headers = {'Authorization': f'Bearer {API_KEY}'}

# Get contacts
response = requests.get(
    'https://api.hubapi.com/crm/v3/objects/contacts',
    headers=headers
)

contacts = response.json()"""
                
                elif "salesforce" in integration_name.lower():
                    return """from simple_salesforce import Salesforce

# Authenticate
sf = Salesforce(
    username='your_username',
    password='your_password',
    security_token='your_token'
)

# Query leads
leads = sf.query("SELECT Id, Name, Email FROM Lead LIMIT 10")"""
        
        return "# Code generation not available for this integration"