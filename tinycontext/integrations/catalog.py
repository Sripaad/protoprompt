"""
Integration Catalog for TinyContext.

Registry and management of available integrations.
"""

from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
from pathlib import Path


class IntegrationType(Enum):
    """Types of integrations."""
    CRM = "crm"
    DATABASE = "database"
    EMAIL = "email"
    API = "api"
    WEBHOOK = "webhook"
    STORAGE = "storage"
    MESSAGING = "messaging"
    ANALYTICS = "analytics"
    PAYMENT = "payment"
    CALENDAR = "calendar"


class AuthMethod(Enum):
    """Authentication methods."""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    TOKEN = "token"
    CONNECTION_STRING = "connection_string"
    CREDENTIALS = "credentials"


@dataclass
class IntegrationDefinition:
    """Definition of an integration."""
    id: str
    name: str
    type: IntegrationType
    provider: str
    description: str
    auth_method: AuthMethod
    connector_class: str
    
    # Configuration
    config_schema: Dict[str, Any] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    
    # Capabilities
    capabilities: List[str] = field(default_factory=list)
    operations: List[str] = field(default_factory=list)
    
    # API Information
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    rate_limits: Dict[str, int] = field(default_factory=dict)
    
    # Documentation
    documentation_url: Optional[str] = None
    setup_guide_url: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    supported_regions: List[str] = field(default_factory=list)
    pricing_tier: str = "free"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "provider": self.provider,
            "description": self.description,
            "auth_method": self.auth_method.value,
            "connector_class": self.connector_class,
            "config_schema": self.config_schema,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "capabilities": self.capabilities,
            "operations": self.operations,
            "base_url": self.base_url,
            "api_version": self.api_version,
            "rate_limits": self.rate_limits,
            "documentation_url": self.documentation_url,
            "setup_guide_url": self.setup_guide_url,
            "tags": self.tags,
            "supported_regions": self.supported_regions,
            "pricing_tier": self.pricing_tier
        }
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate configuration against schema.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate field types if schema provided
        if self.config_schema:
            for field, expected_type in self.config_schema.items():
                if field in config:
                    actual_type = type(config[field]).__name__
                    if actual_type != expected_type and expected_type != "any":
                        errors.append(f"Field '{field}' should be {expected_type}, got {actual_type}")
        
        return len(errors) == 0, errors


class IntegrationCatalog:
    """
    Catalog of available integrations.
    
    Manages registration, discovery, and instantiation of integrations.
    """
    
    def __init__(self, catalog_path: Optional[Path] = None):
        """
        Initialize integration catalog.
        
        Args:
            catalog_path: Path to catalog definitions
        """
        self.catalog_path = catalog_path
        self.integrations: Dict[str, IntegrationDefinition] = {}
        self.connectors: Dict[str, Type] = {}
        
        # Load built-in integrations
        self._load_builtin_integrations()
        
        # Load custom integrations
        if catalog_path and catalog_path.exists():
            self._load_custom_integrations(catalog_path)
    
    def _load_builtin_integrations(self):
        """Load built-in integration definitions."""
        
        # Salesforce
        self.register_integration(IntegrationDefinition(
            id="salesforce",
            name="Salesforce",
            type=IntegrationType.CRM,
            provider="Salesforce",
            description="Enterprise CRM platform",
            auth_method=AuthMethod.OAUTH2,
            connector_class="tinycontext.integrations.connectors.crm_connector.SalesforceConnector",
            config_schema={
                "client_id": "str",
                "client_secret": "str",
                "username": "str",
                "password": "str",
                "security_token": "str",
                "sandbox": "bool"
            },
            required_fields=["client_id", "client_secret", "username", "password"],
            optional_fields=["security_token", "sandbox"],
            capabilities=["contacts", "leads", "opportunities", "accounts", "custom_objects"],
            operations=["create", "read", "update", "delete", "bulk", "query"],
            base_url="https://login.salesforce.com",
            api_version="v58.0",
            rate_limits={"daily": 15000, "concurrent": 25},
            documentation_url="https://developer.salesforce.com/docs/apis",
            tags=["enterprise", "crm", "sales"],
            pricing_tier="paid"
        ))
        
        # HubSpot
        self.register_integration(IntegrationDefinition(
            id="hubspot",
            name="HubSpot",
            type=IntegrationType.CRM,
            provider="HubSpot",
            description="Inbound marketing and sales platform",
            auth_method=AuthMethod.API_KEY,
            connector_class="tinycontext.integrations.connectors.crm_connector.HubSpotConnector",
            config_schema={
                "api_key": "str",
                "portal_id": "str"
            },
            required_fields=["api_key"],
            optional_fields=["portal_id"],
            capabilities=["contacts", "companies", "deals", "tickets", "marketing"],
            operations=["create", "read", "update", "delete", "batch", "search"],
            base_url="https://api.hubapi.com",
            api_version="v3",
            rate_limits={"per_second": 10, "per_day": 250000},
            documentation_url="https://developers.hubspot.com/docs/api",
            tags=["marketing", "crm", "sales", "inbound"],
            pricing_tier="freemium"
        ))
        
        # PostgreSQL
        self.register_integration(IntegrationDefinition(
            id="postgresql",
            name="PostgreSQL",
            type=IntegrationType.DATABASE,
            provider="PostgreSQL",
            description="Open-source relational database",
            auth_method=AuthMethod.CONNECTION_STRING,
            connector_class="tinycontext.integrations.connectors.sql_connector.PostgreSQLConnector",
            config_schema={
                "host": "str",
                "port": "int",
                "database": "str",
                "username": "str",
                "password": "str",
                "ssl_mode": "str"
            },
            required_fields=["host", "database", "username", "password"],
            optional_fields=["port", "ssl_mode"],
            capabilities=["sql", "transactions", "json", "full_text_search"],
            operations=["query", "insert", "update", "delete", "bulk_insert", "transaction"],
            documentation_url="https://www.postgresql.org/docs/",
            tags=["database", "sql", "relational", "open_source"],
            pricing_tier="free"
        ))
        
        # MongoDB
        self.register_integration(IntegrationDefinition(
            id="mongodb",
            name="MongoDB",
            type=IntegrationType.DATABASE,
            provider="MongoDB",
            description="NoSQL document database",
            auth_method=AuthMethod.CONNECTION_STRING,
            connector_class="tinycontext.integrations.connectors.nosql_connector.MongoDBConnector",
            config_schema={
                "connection_string": "str",
                "database": "str"
            },
            required_fields=["connection_string", "database"],
            capabilities=["documents", "aggregation", "text_search", "geospatial"],
            operations=["find", "insert", "update", "delete", "aggregate", "bulk_write"],
            documentation_url="https://docs.mongodb.com/",
            tags=["database", "nosql", "document", "scalable"],
            pricing_tier="freemium"
        ))
        
        # SendGrid
        self.register_integration(IntegrationDefinition(
            id="sendgrid",
            name="SendGrid",
            type=IntegrationType.EMAIL,
            provider="Twilio",
            description="Email delivery service",
            auth_method=AuthMethod.API_KEY,
            connector_class="tinycontext.integrations.connectors.email_connector.SendGridConnector",
            config_schema={
                "api_key": "str",
                "from_email": "str",
                "from_name": "str"
            },
            required_fields=["api_key", "from_email"],
            optional_fields=["from_name"],
            capabilities=["transactional", "marketing", "templates", "analytics"],
            operations=["send", "send_bulk", "schedule", "template"],
            base_url="https://api.sendgrid.com",
            api_version="v3",
            rate_limits={"per_second": 100, "per_day": 100000},
            documentation_url="https://sendgrid.com/docs/api-reference/",
            tags=["email", "transactional", "marketing", "delivery"],
            pricing_tier="freemium"
        ))
        
        # Slack
        self.register_integration(IntegrationDefinition(
            id="slack",
            name="Slack",
            type=IntegrationType.MESSAGING,
            provider="Slack",
            description="Team communication platform",
            auth_method=AuthMethod.TOKEN,
            connector_class="tinycontext.integrations.connectors.messaging_connector.SlackConnector",
            config_schema={
                "bot_token": "str",
                "app_token": "str",
                "webhook_url": "str"
            },
            required_fields=["bot_token"],
            optional_fields=["app_token", "webhook_url"],
            capabilities=["messages", "channels", "users", "files", "webhooks"],
            operations=["send_message", "create_channel", "upload_file", "list_users"],
            base_url="https://slack.com/api",
            documentation_url="https://api.slack.com/",
            tags=["messaging", "collaboration", "notifications"],
            pricing_tier="freemium"
        ))
        
        # Google Sheets
        self.register_integration(IntegrationDefinition(
            id="google_sheets",
            name="Google Sheets",
            type=IntegrationType.STORAGE,
            provider="Google",
            description="Online spreadsheet service",
            auth_method=AuthMethod.OAUTH2,
            connector_class="tinycontext.integrations.connectors.storage_connector.GoogleSheetsConnector",
            config_schema={
                "credentials_json": "str",
                "spreadsheet_id": "str"
            },
            required_fields=["credentials_json", "spreadsheet_id"],
            capabilities=["spreadsheets", "formulas", "charts", "collaboration"],
            operations=["read", "write", "append", "clear", "format"],
            base_url="https://sheets.googleapis.com",
            api_version="v4",
            documentation_url="https://developers.google.com/sheets/api",
            tags=["spreadsheet", "storage", "collaboration"],
            pricing_tier="free"
        ))
    
    def register_integration(self, definition: IntegrationDefinition):
        """
        Register an integration definition.
        
        Args:
            definition: Integration definition
        """
        self.integrations[definition.id] = definition
    
    def get_integration(self, integration_id: str) -> Optional[IntegrationDefinition]:
        """
        Get integration definition by ID.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Integration definition or None
        """
        return self.integrations.get(integration_id)
    
    def search_integrations(
        self,
        type: Optional[IntegrationType] = None,
        capabilities: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> List[IntegrationDefinition]:
        """
        Search for integrations matching criteria.
        
        Args:
            type: Integration type filter
            capabilities: Required capabilities
            tags: Required tags
            
        Returns:
            List of matching integrations
        """
        results = []
        
        for integration in self.integrations.values():
            # Type filter
            if type and integration.type != type:
                continue
            
            # Capabilities filter
            if capabilities:
                if not all(cap in integration.capabilities for cap in capabilities):
                    continue
            
            # Tags filter
            if tags:
                if not any(tag in integration.tags for tag in tags):
                    continue
            
            results.append(integration)
        
        return results
    
    def get_by_type(self, type: IntegrationType) -> List[IntegrationDefinition]:
        """Get all integrations of a specific type."""
        return [i for i in self.integrations.values() if i.type == type]
    
    def get_by_provider(self, provider: str) -> List[IntegrationDefinition]:
        """Get all integrations from a specific provider."""
        return [i for i in self.integrations.values() if i.provider == provider]
    
    def validate_config(
        self,
        integration_id: str,
        config: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate configuration for an integration.
        
        Args:
            integration_id: Integration ID
            config: Configuration to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        integration = self.get_integration(integration_id)
        if not integration:
            return False, [f"Integration '{integration_id}' not found"]
        
        return integration.validate_config(config)
    
    def _load_custom_integrations(self, catalog_path: Path):
        """Load custom integration definitions from files."""
        for file_path in catalog_path.glob("*.yaml"):
            try:
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
                    
                    # Convert to IntegrationDefinition
                    definition = IntegrationDefinition(
                        id=data["id"],
                        name=data["name"],
                        type=IntegrationType(data["type"]),
                        provider=data["provider"],
                        description=data.get("description", ""),
                        auth_method=AuthMethod(data["auth_method"]),
                        connector_class=data["connector_class"],
                        **{k: v for k, v in data.items() if k not in 
                           ["id", "name", "type", "provider", "description", 
                            "auth_method", "connector_class"]}
                    )
                    
                    self.register_integration(definition)
            except Exception as e:
                print(f"Error loading integration from {file_path}: {e}")
    
    def export_catalog(self, format: str = "json") -> str:
        """Export catalog in specified format."""
        catalog_data = {
            id: definition.to_dict()
            for id, definition in self.integrations.items()
        }
        
        if format == "json":
            return json.dumps(catalog_data, indent=2)
        elif format == "yaml":
            return yaml.dump(catalog_data, default_flow_style=False)
        else:
            return str(catalog_data)
    
    def get_setup_instructions(self, integration_id: str) -> Dict[str, Any]:
        """
        Get setup instructions for an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Setup instructions
        """
        integration = self.get_integration(integration_id)
        if not integration:
            return {"error": f"Integration '{integration_id}' not found"}
        
        return {
            "integration": integration.name,
            "auth_method": integration.auth_method.value,
            "required_fields": integration.required_fields,
            "optional_fields": integration.optional_fields,
            "documentation": integration.documentation_url,
            "setup_guide": integration.setup_guide_url,
            "example_config": self._generate_example_config(integration)
        }
    
    def _generate_example_config(self, integration: IntegrationDefinition) -> Dict[str, Any]:
        """Generate example configuration."""
        config = {}
        
        for field in integration.required_fields:
            if field in integration.config_schema:
                field_type = integration.config_schema[field]
                if field_type == "str":
                    config[field] = f"your_{field}"
                elif field_type == "int":
                    config[field] = 0
                elif field_type == "bool":
                    config[field] = False
            else:
                config[field] = f"<{field}>"
        
        return config