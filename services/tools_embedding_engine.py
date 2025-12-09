# -*- coding: utf-8 -*-
"""
Sprint B3-A: Tools Embedding Engine & Discovery

Semantic discovery engine for AI tools using embeddings.

Features:
- Embedding model integration (OpenAI text-embedding-3-large or fallback)
- Tool vector generation and caching
- Semantic search for use cases
- Automatic clustering with label generation
- Similarity scoring

Version: 1.0.0 (Sprint B3)
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
from dataclasses import dataclass, field, asdict
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

TOOLS_EMBEDDING_ENABLED = os.getenv("TOOLS_EMBEDDING_ENABLED", "1").lower() in ("1", "true", "yes")
TOOLS_EMBEDDING_MODEL = os.getenv("TOOLS_EMBEDDING_MODEL", "text-embedding-3-large")
TOOLS_EMBEDDING_CACHE_ENABLED = os.getenv("TOOLS_EMBEDDING_CACHE_ENABLED", "1").lower() in ("1", "true", "yes")
TOOLS_CLUSTER_COUNT = int(os.getenv("TOOLS_CLUSTER_COUNT", "8"))
TOOLS_EMBEDDING_DIMENSION = int(os.getenv("TOOLS_EMBEDDING_DIMENSION", "256"))  # Reduced for efficiency

# Cache directory for embeddings
EMBEDDING_CACHE_DIR = os.getenv(
    "EMBEDDING_CACHE_DIR",
    os.path.join(os.path.dirname(__file__), "..", "data", "embeddings_cache")
)

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ToolEmbedding:
    """Embedded representation of a tool."""
    tool_name: str
    tool_id: str
    description: str
    categories: List[str] = field(default_factory=list)
    sector_usecases: List[str] = field(default_factory=list)
    embedding: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolCluster:
    """A cluster of semantically related tools."""
    cluster_id: int
    label: str
    description: str
    tool_names: List[str] = field(default_factory=list)
    centroid: List[float] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticSearchResult:
    """Result from semantic search."""
    tool_name: str
    tool_id: str
    similarity_score: float
    categories: List[str] = field(default_factory=list)
    description: str = ""
    cluster_label: str = ""


# =============================================================================
# COMPREHENSIVE TOOL DATABASE
# =============================================================================

# Extended tool database with descriptions and metadata
TOOL_DATABASE: List[Dict[str, Any]] = [
    # Content Generation & Writing
    {
        "name": "ChatGPT",
        "id": "chatgpt",
        "description": "Versatile AI assistant for text generation, analysis, coding, and creative tasks",
        "categories": ["content", "coding", "analysis", "automation"],
        "usecases": ["content creation", "code assistance", "research", "customer support"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Claude",
        "id": "claude",
        "description": "Advanced AI assistant with strong reasoning and analysis capabilities",
        "categories": ["content", "analysis", "coding", "research"],
        "usecases": ["document analysis", "code review", "research synthesis", "writing"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Jasper",
        "id": "jasper",
        "description": "AI content platform for marketing copy, blog posts, and brand content",
        "categories": ["content", "marketing", "copywriting"],
        "usecases": ["marketing copy", "blog posts", "ad copy", "social media"],
        "complexity": "low",
        "pricing": "paid",
    },
    {
        "name": "Copy.ai",
        "id": "copy_ai",
        "description": "AI copywriting tool for marketing and sales content",
        "categories": ["content", "marketing", "sales"],
        "usecases": ["email copy", "product descriptions", "social posts", "ad copy"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Writesonic",
        "id": "writesonic",
        "description": "AI writing assistant for articles, ads, and marketing content",
        "categories": ["content", "marketing", "seo"],
        "usecases": ["blog articles", "landing pages", "product descriptions", "ads"],
        "complexity": "low",
        "pricing": "freemium",
    },
    # Research & Analysis
    {
        "name": "Perplexity AI",
        "id": "perplexity",
        "description": "AI-powered research assistant with real-time web search",
        "categories": ["research", "search", "analysis"],
        "usecases": ["market research", "competitive analysis", "fact checking", "trend analysis"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Consensus",
        "id": "consensus",
        "description": "AI search engine for scientific research and academic papers",
        "categories": ["research", "academic", "analysis"],
        "usecases": ["literature review", "scientific research", "evidence synthesis"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Elicit",
        "id": "elicit",
        "description": "AI research assistant for finding and synthesizing papers",
        "categories": ["research", "academic", "analysis"],
        "usecases": ["systematic reviews", "research synthesis", "paper discovery"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    # Automation & Workflow
    {
        "name": "Make (Integromat)",
        "id": "make",
        "description": "Visual automation platform for connecting apps and workflows",
        "categories": ["automation", "integration", "workflow"],
        "usecases": ["workflow automation", "data sync", "app integration", "process automation"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    {
        "name": "Zapier",
        "id": "zapier",
        "description": "No-code automation tool for connecting apps",
        "categories": ["automation", "integration", "workflow"],
        "usecases": ["task automation", "data transfer", "notifications", "lead routing"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "n8n",
        "id": "n8n",
        "description": "Open-source workflow automation with self-hosting option",
        "categories": ["automation", "integration", "workflow", "open-source"],
        "usecases": ["workflow automation", "data pipelines", "self-hosted automation"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    {
        "name": "Power Automate",
        "id": "power_automate",
        "description": "Microsoft's automation platform for business processes",
        "categories": ["automation", "microsoft", "enterprise"],
        "usecases": ["document workflows", "approval processes", "data collection"],
        "complexity": "medium",
        "pricing": "paid",
    },
    # Meeting & Collaboration
    {
        "name": "Fireflies.ai",
        "id": "fireflies",
        "description": "AI meeting assistant for transcription and note-taking",
        "categories": ["meeting", "transcription", "collaboration"],
        "usecases": ["meeting notes", "action items", "searchable transcripts"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Otter.ai",
        "id": "otter",
        "description": "AI-powered meeting transcription and notes",
        "categories": ["meeting", "transcription", "productivity"],
        "usecases": ["meeting transcription", "interview notes", "lecture capture"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Krisp",
        "id": "krisp",
        "description": "AI noise cancellation for calls and meetings",
        "categories": ["meeting", "audio", "productivity"],
        "usecases": ["noise removal", "call quality", "remote work"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Loom",
        "id": "loom",
        "description": "Async video messaging for team communication",
        "categories": ["video", "communication", "collaboration"],
        "usecases": ["video updates", "tutorials", "feedback", "async communication"],
        "complexity": "low",
        "pricing": "freemium",
    },
    # Design & Visual
    {
        "name": "Canva",
        "id": "canva",
        "description": "AI-powered design platform for graphics and presentations",
        "categories": ["design", "visual", "marketing"],
        "usecases": ["social graphics", "presentations", "marketing materials"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Midjourney",
        "id": "midjourney",
        "description": "AI image generation for creative and marketing visuals",
        "categories": ["design", "image-generation", "creative"],
        "usecases": ["concept art", "marketing images", "creative exploration"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "DALL-E",
        "id": "dalle",
        "description": "OpenAI's image generation model for creating visuals from text",
        "categories": ["design", "image-generation", "creative"],
        "usecases": ["product mockups", "marketing visuals", "creative content"],
        "complexity": "low",
        "pricing": "paid",
    },
    {
        "name": "Figma",
        "id": "figma",
        "description": "Collaborative design tool with AI features",
        "categories": ["design", "ui-ux", "collaboration"],
        "usecases": ["ui design", "prototyping", "design systems"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    # Data & Analytics
    {
        "name": "Tableau",
        "id": "tableau",
        "description": "Business intelligence and data visualization platform",
        "categories": ["analytics", "visualization", "bi"],
        "usecases": ["dashboards", "data analysis", "reporting", "insights"],
        "complexity": "high",
        "pricing": "paid",
    },
    {
        "name": "Power BI",
        "id": "power_bi",
        "description": "Microsoft's business analytics service",
        "categories": ["analytics", "visualization", "microsoft"],
        "usecases": ["business dashboards", "data modeling", "reporting"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    {
        "name": "Obviously AI",
        "id": "obviously_ai",
        "description": "No-code machine learning for predictions",
        "categories": ["analytics", "ml", "no-code"],
        "usecases": ["sales forecasting", "churn prediction", "demand planning"],
        "complexity": "low",
        "pricing": "paid",
    },
    {
        "name": "MonkeyLearn",
        "id": "monkeylearn",
        "description": "Text analysis and sentiment analysis platform",
        "categories": ["analytics", "nlp", "text-analysis"],
        "usecases": ["sentiment analysis", "topic classification", "keyword extraction"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    # Customer Service
    {
        "name": "Intercom",
        "id": "intercom",
        "description": "AI-powered customer messaging platform",
        "categories": ["customer-service", "chatbot", "support"],
        "usecases": ["live chat", "chatbots", "help desk", "customer engagement"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Zendesk",
        "id": "zendesk",
        "description": "Customer service platform with AI capabilities",
        "categories": ["customer-service", "ticketing", "support"],
        "usecases": ["ticket management", "knowledge base", "chat support"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Drift",
        "id": "drift",
        "description": "Conversational marketing and sales platform",
        "categories": ["customer-service", "sales", "chatbot"],
        "usecases": ["lead qualification", "meeting booking", "sales chat"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Freshdesk",
        "id": "freshdesk",
        "description": "Cloud-based customer support software",
        "categories": ["customer-service", "ticketing", "support"],
        "usecases": ["ticket management", "self-service", "automation"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    # Coding & Development
    {
        "name": "GitHub Copilot",
        "id": "github_copilot",
        "description": "AI pair programmer for code completion and generation",
        "categories": ["coding", "development", "automation"],
        "usecases": ["code completion", "code generation", "documentation"],
        "complexity": "low",
        "pricing": "paid",
    },
    {
        "name": "Cursor",
        "id": "cursor",
        "description": "AI-first code editor for developers",
        "categories": ["coding", "development", "ide"],
        "usecases": ["code editing", "refactoring", "debugging"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    {
        "name": "Tabnine",
        "id": "tabnine",
        "description": "AI code completion for multiple languages",
        "categories": ["coding", "development", "automation"],
        "usecases": ["code completion", "code suggestions", "learning"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Replit",
        "id": "replit",
        "description": "Browser-based IDE with AI assistance",
        "categories": ["coding", "development", "cloud"],
        "usecases": ["prototyping", "learning", "collaboration"],
        "complexity": "low",
        "pricing": "freemium",
    },
    # Project Management
    {
        "name": "Notion AI",
        "id": "notion_ai",
        "description": "AI-enhanced workspace for notes and project management",
        "categories": ["productivity", "documentation", "project-management"],
        "usecases": ["documentation", "wikis", "task management", "note-taking"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "ClickUp",
        "id": "clickup",
        "description": "All-in-one project management with AI features",
        "categories": ["project-management", "productivity", "collaboration"],
        "usecases": ["task management", "docs", "goals", "time tracking"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    {
        "name": "Monday.com",
        "id": "monday",
        "description": "Work OS with AI automation capabilities",
        "categories": ["project-management", "workflow", "collaboration"],
        "usecases": ["project tracking", "resource planning", "automation"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Asana",
        "id": "asana",
        "description": "Work management platform with AI features",
        "categories": ["project-management", "productivity", "collaboration"],
        "usecases": ["task management", "project planning", "team coordination"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    # Sales & CRM
    {
        "name": "HubSpot",
        "id": "hubspot",
        "description": "CRM platform with AI-powered sales and marketing tools",
        "categories": ["crm", "sales", "marketing"],
        "usecases": ["lead management", "email marketing", "sales automation"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    {
        "name": "Salesforce Einstein",
        "id": "salesforce_einstein",
        "description": "AI layer for Salesforce CRM",
        "categories": ["crm", "sales", "enterprise"],
        "usecases": ["lead scoring", "forecasting", "recommendations"],
        "complexity": "high",
        "pricing": "paid",
    },
    {
        "name": "Gong",
        "id": "gong",
        "description": "Revenue intelligence platform with conversation AI",
        "categories": ["sales", "analytics", "coaching"],
        "usecases": ["call analysis", "deal intelligence", "sales coaching"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Apollo.io",
        "id": "apollo",
        "description": "Sales intelligence and engagement platform",
        "categories": ["sales", "prospecting", "outreach"],
        "usecases": ["lead generation", "email sequences", "data enrichment"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    # Email & Communication
    {
        "name": "Superhuman",
        "id": "superhuman",
        "description": "AI-powered email client for productivity",
        "categories": ["email", "productivity", "communication"],
        "usecases": ["email management", "inbox zero", "scheduling"],
        "complexity": "low",
        "pricing": "paid",
    },
    {
        "name": "Grammarly",
        "id": "grammarly",
        "description": "AI writing assistant for grammar and style",
        "categories": ["writing", "productivity", "communication"],
        "usecases": ["grammar check", "tone adjustment", "clarity"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Mailchimp",
        "id": "mailchimp",
        "description": "Email marketing platform with AI optimization",
        "categories": ["email", "marketing", "automation"],
        "usecases": ["email campaigns", "audience segmentation", "automation"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    # Finance & Accounting
    {
        "name": "Xero",
        "id": "xero",
        "description": "Cloud accounting software with AI features",
        "categories": ["finance", "accounting", "automation"],
        "usecases": ["invoicing", "bank reconciliation", "expense tracking"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "QuickBooks",
        "id": "quickbooks",
        "description": "Accounting software for small businesses",
        "categories": ["finance", "accounting", "invoicing"],
        "usecases": ["bookkeeping", "invoicing", "payroll", "reporting"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Expensify",
        "id": "expensify",
        "description": "AI-powered expense management",
        "categories": ["finance", "expense", "automation"],
        "usecases": ["receipt scanning", "expense reports", "reimbursement"],
        "complexity": "low",
        "pricing": "freemium",
    },
    # HR & Recruitment
    {
        "name": "Greenhouse",
        "id": "greenhouse",
        "description": "Hiring platform with AI-powered sourcing",
        "categories": ["hr", "recruitment", "ats"],
        "usecases": ["applicant tracking", "interview scheduling", "analytics"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Textio",
        "id": "textio",
        "description": "AI writing platform for job descriptions",
        "categories": ["hr", "writing", "recruitment"],
        "usecases": ["job postings", "inclusive language", "performance reviews"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Workday",
        "id": "workday",
        "description": "Enterprise HR and finance cloud platform",
        "categories": ["hr", "enterprise", "finance"],
        "usecases": ["hcm", "payroll", "talent management", "analytics"],
        "complexity": "high",
        "pricing": "paid",
    },
    # Legal & Compliance
    {
        "name": "Harvey",
        "id": "harvey",
        "description": "AI assistant for legal professionals",
        "categories": ["legal", "compliance", "research"],
        "usecases": ["contract review", "legal research", "due diligence"],
        "complexity": "high",
        "pricing": "paid",
    },
    {
        "name": "ContractPodAi",
        "id": "contractpod",
        "description": "AI-powered contract lifecycle management",
        "categories": ["legal", "contracts", "automation"],
        "usecases": ["contract creation", "clause library", "risk analysis"],
        "complexity": "high",
        "pricing": "paid",
    },
    {
        "name": "Kira Systems",
        "id": "kira",
        "description": "Machine learning for contract analysis",
        "categories": ["legal", "contracts", "ml"],
        "usecases": ["due diligence", "contract review", "data extraction"],
        "complexity": "high",
        "pricing": "paid",
    },
    # Security & Governance
    {
        "name": "Darktrace",
        "id": "darktrace",
        "description": "AI cyber security for threat detection",
        "categories": ["security", "ai", "enterprise"],
        "usecases": ["threat detection", "incident response", "network security"],
        "complexity": "high",
        "pricing": "paid",
    },
    {
        "name": "Snyk",
        "id": "snyk",
        "description": "Developer security platform",
        "categories": ["security", "development", "devops"],
        "usecases": ["vulnerability scanning", "dependency check", "container security"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    {
        "name": "OneTrust",
        "id": "onetrust",
        "description": "Privacy and data governance platform",
        "categories": ["compliance", "privacy", "governance"],
        "usecases": ["gdpr compliance", "consent management", "data mapping"],
        "complexity": "high",
        "pricing": "paid",
    },
    # Industry-Specific: Construction
    {
        "name": "Procore",
        "id": "procore",
        "description": "Construction management platform",
        "categories": ["construction", "project-management", "industry"],
        "usecases": ["project management", "document control", "quality management"],
        "complexity": "high",
        "pricing": "paid",
    },
    {
        "name": "PlanRadar",
        "id": "planradar",
        "description": "Construction documentation and defect management",
        "categories": ["construction", "documentation", "quality"],
        "usecases": ["defect tracking", "site documentation", "reporting"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "BIM 360",
        "id": "bim360",
        "description": "Autodesk's construction management cloud",
        "categories": ["construction", "bim", "collaboration"],
        "usecases": ["bim coordination", "document management", "field management"],
        "complexity": "high",
        "pricing": "paid",
    },
    # Industry-Specific: Healthcare
    {
        "name": "Nuance DAX",
        "id": "nuance_dax",
        "description": "AI clinical documentation for healthcare",
        "categories": ["healthcare", "documentation", "voice"],
        "usecases": ["clinical notes", "voice dictation", "ehr integration"],
        "complexity": "high",
        "pricing": "paid",
    },
    {
        "name": "Meditech",
        "id": "meditech",
        "description": "Healthcare information system",
        "categories": ["healthcare", "ehr", "enterprise"],
        "usecases": ["patient records", "clinical workflows", "billing"],
        "complexity": "high",
        "pricing": "paid",
    },
    # Industry-Specific: Logistics
    {
        "name": "Route4Me",
        "id": "route4me",
        "description": "Route optimization and planning software",
        "categories": ["logistics", "routing", "optimization"],
        "usecases": ["route planning", "delivery optimization", "fleet management"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Project44",
        "id": "project44",
        "description": "Supply chain visibility platform",
        "categories": ["logistics", "supply-chain", "tracking"],
        "usecases": ["shipment tracking", "eta prediction", "carrier management"],
        "complexity": "high",
        "pricing": "paid",
    },
    {
        "name": "Flexport",
        "id": "flexport",
        "description": "Freight forwarding and supply chain platform",
        "categories": ["logistics", "freight", "supply-chain"],
        "usecases": ["freight booking", "customs", "supply chain analytics"],
        "complexity": "high",
        "pricing": "paid",
    },
    # Industry-Specific: Finance
    {
        "name": "Plaid",
        "id": "plaid",
        "description": "Financial data connectivity platform",
        "categories": ["fintech", "api", "data"],
        "usecases": ["bank connections", "payment verification", "financial data"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Stripe",
        "id": "stripe",
        "description": "Payment processing infrastructure",
        "categories": ["fintech", "payments", "api"],
        "usecases": ["payment processing", "subscriptions", "invoicing"],
        "complexity": "medium",
        "pricing": "usage-based",
    },
    # Video & Media
    {
        "name": "Synthesia",
        "id": "synthesia",
        "description": "AI video generation with avatars",
        "categories": ["video", "ai-generation", "marketing"],
        "usecases": ["training videos", "marketing videos", "personalization"],
        "complexity": "low",
        "pricing": "paid",
    },
    {
        "name": "Descript",
        "id": "descript",
        "description": "AI-powered video and audio editing",
        "categories": ["video", "audio", "editing"],
        "usecases": ["podcast editing", "video editing", "transcription"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    {
        "name": "Runway",
        "id": "runway",
        "description": "AI creative tools for video and image generation",
        "categories": ["video", "ai-generation", "creative"],
        "usecases": ["video generation", "image editing", "visual effects"],
        "complexity": "medium",
        "pricing": "freemium",
    },
    # SEO & Marketing Analytics
    {
        "name": "Semrush",
        "id": "semrush",
        "description": "SEO and marketing analytics platform",
        "categories": ["seo", "marketing", "analytics"],
        "usecases": ["keyword research", "competitor analysis", "site audit"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Ahrefs",
        "id": "ahrefs",
        "description": "SEO toolset for backlinks and keywords",
        "categories": ["seo", "marketing", "research"],
        "usecases": ["backlink analysis", "keyword research", "rank tracking"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Clearscope",
        "id": "clearscope",
        "description": "AI content optimization for SEO",
        "categories": ["seo", "content", "optimization"],
        "usecases": ["content optimization", "keyword targeting", "content grading"],
        "complexity": "medium",
        "pricing": "paid",
    },
    # Social Media
    {
        "name": "Buffer",
        "id": "buffer",
        "description": "Social media management and scheduling",
        "categories": ["social-media", "marketing", "automation"],
        "usecases": ["post scheduling", "analytics", "engagement"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Hootsuite",
        "id": "hootsuite",
        "description": "Social media management platform",
        "categories": ["social-media", "marketing", "enterprise"],
        "usecases": ["social scheduling", "monitoring", "analytics"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "Sprout Social",
        "id": "sprout_social",
        "description": "Social media management with AI insights",
        "categories": ["social-media", "analytics", "enterprise"],
        "usecases": ["social publishing", "listening", "analytics"],
        "complexity": "medium",
        "pricing": "paid",
    },
    # Data Quality & ETL
    {
        "name": "Fivetran",
        "id": "fivetran",
        "description": "Automated data integration and ETL",
        "categories": ["data", "etl", "integration"],
        "usecases": ["data pipelines", "warehouse loading", "sync"],
        "complexity": "medium",
        "pricing": "paid",
    },
    {
        "name": "dbt",
        "id": "dbt",
        "description": "Data transformation tool for analytics",
        "categories": ["data", "analytics", "transformation"],
        "usecases": ["data modeling", "transformation", "documentation"],
        "complexity": "high",
        "pricing": "freemium",
    },
    {
        "name": "Great Expectations",
        "id": "great_expectations",
        "description": "Data quality and validation framework",
        "categories": ["data", "quality", "testing"],
        "usecases": ["data validation", "quality checks", "documentation"],
        "complexity": "high",
        "pricing": "open-source",
    },
    # MLOps & AI Infrastructure
    {
        "name": "MLflow",
        "id": "mlflow",
        "description": "Open-source ML lifecycle management",
        "categories": ["mlops", "ml", "infrastructure"],
        "usecases": ["experiment tracking", "model registry", "deployment"],
        "complexity": "high",
        "pricing": "open-source",
    },
    {
        "name": "Weights & Biases",
        "id": "wandb",
        "description": "ML experiment tracking and visualization",
        "categories": ["mlops", "ml", "monitoring"],
        "usecases": ["experiment tracking", "model monitoring", "collaboration"],
        "complexity": "high",
        "pricing": "freemium",
    },
    {
        "name": "Hugging Face",
        "id": "huggingface",
        "description": "AI model hub and deployment platform",
        "categories": ["mlops", "ml", "models"],
        "usecases": ["model hosting", "fine-tuning", "inference"],
        "complexity": "high",
        "pricing": "freemium",
    },
    # Forms & Surveys
    {
        "name": "Typeform",
        "id": "typeform",
        "description": "Interactive form and survey builder",
        "categories": ["forms", "surveys", "marketing"],
        "usecases": ["surveys", "lead capture", "quizzes", "feedback"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Tally",
        "id": "tally",
        "description": "Free form builder with no limits",
        "categories": ["forms", "surveys", "free"],
        "usecases": ["forms", "surveys", "data collection"],
        "complexity": "low",
        "pricing": "freemium",
    },
    # Presentation & Documents
    {
        "name": "Beautiful.ai",
        "id": "beautiful_ai",
        "description": "AI-powered presentation software",
        "categories": ["presentation", "design", "productivity"],
        "usecases": ["slide decks", "pitch decks", "reports"],
        "complexity": "low",
        "pricing": "paid",
    },
    {
        "name": "Gamma",
        "id": "gamma",
        "description": "AI presentation and document generator",
        "categories": ["presentation", "ai-generation", "content"],
        "usecases": ["presentations", "documents", "websites"],
        "complexity": "low",
        "pricing": "freemium",
    },
    {
        "name": "Tome",
        "id": "tome",
        "description": "AI-powered storytelling and presentations",
        "categories": ["presentation", "ai-generation", "storytelling"],
        "usecases": ["presentations", "proposals", "reports"],
        "complexity": "low",
        "pricing": "freemium",
    },
]


# =============================================================================
# CLUSTER DEFINITIONS
# =============================================================================

# Pre-defined cluster labels and keywords for deterministic clustering
CLUSTER_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": 0,
        "label": "Content Generation",
        "description": "Tools for creating written content, copy, and text",
        "keywords": ["content", "writing", "copy", "text", "generation", "blog", "article"],
        "categories": ["content", "copywriting", "writing"],
    },
    {
        "id": 1,
        "label": "Automation & Workflow",
        "description": "Tools for automating tasks and connecting applications",
        "keywords": ["automation", "workflow", "integration", "zapier", "automate", "process"],
        "categories": ["automation", "integration", "workflow"],
    },
    {
        "id": 2,
        "label": "Research & Analysis",
        "description": "Tools for research, data analysis, and insights",
        "keywords": ["research", "analysis", "data", "insights", "analytics", "intelligence"],
        "categories": ["research", "analytics", "analysis"],
    },
    {
        "id": 3,
        "label": "Meeting & Collaboration",
        "description": "Tools for meetings, communication, and teamwork",
        "keywords": ["meeting", "collaboration", "communication", "team", "video", "call"],
        "categories": ["meeting", "collaboration", "communication", "video"],
    },
    {
        "id": 4,
        "label": "Design & Visual",
        "description": "Tools for design, images, and visual content",
        "keywords": ["design", "visual", "image", "graphics", "creative", "ui"],
        "categories": ["design", "visual", "image-generation", "ui-ux"],
    },
    {
        "id": 5,
        "label": "Sales & CRM",
        "description": "Tools for sales, customer relationships, and revenue",
        "keywords": ["sales", "crm", "customer", "lead", "revenue", "pipeline"],
        "categories": ["sales", "crm", "prospecting"],
    },
    {
        "id": 6,
        "label": "Development & Coding",
        "description": "Tools for software development and coding",
        "keywords": ["code", "development", "programming", "developer", "software", "ide"],
        "categories": ["coding", "development", "devops"],
    },
    {
        "id": 7,
        "label": "Governance & Security",
        "description": "Tools for compliance, security, and governance",
        "keywords": ["security", "compliance", "governance", "privacy", "audit", "legal"],
        "categories": ["security", "compliance", "governance", "legal"],
    },
]


# =============================================================================
# EMBEDDING FUNCTIONS
# =============================================================================

def _get_text_for_embedding(tool: Dict[str, Any]) -> str:
    """Generate text representation for embedding."""
    parts = [
        tool.get("name", ""),
        tool.get("description", ""),
        " ".join(tool.get("categories", [])),
        " ".join(tool.get("usecases", [])),
    ]
    return " ".join(parts)


def _simple_text_to_vector(text: str, dimension: int = 256) -> List[float]:
    """
    Generate a simple deterministic vector from text.

    Uses character-based hashing for deterministic results.
    This is a fallback when no embedding API is available.
    """
    if not text:
        return [0.0] * dimension

    # Normalize text
    text = text.lower().strip()

    # Create hash-based vector
    vector = []
    for i in range(dimension):
        # Use different hash seeds for each dimension
        h = hashlib.md5(f"{text}_{i}".encode()).hexdigest()
        # Convert to float in range [-1, 1]
        val = (int(h[:8], 16) / 0xFFFFFFFF) * 2 - 1
        vector.append(val)

    # Normalize to unit vector
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]

    return vector


def _get_openai_embedding(text: str) -> Optional[List[float]]:
    """Get embedding from OpenAI API (if available)."""
    try:
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model=TOOLS_EMBEDDING_MODEL,
            input=text,
            dimensions=TOOLS_EMBEDDING_DIMENSION,
        )
        return response.data[0].embedding
    except Exception as e:
        log.debug("[B3] OpenAI embedding failed: %s", e)
        return None


def get_embedding(text: str, use_cache: bool = True) -> List[float]:
    """
    Get embedding for text.

    Tries OpenAI API first, falls back to simple vector.
    """
    if not text:
        return [0.0] * TOOLS_EMBEDDING_DIMENSION

    # Try cache first
    if use_cache and TOOLS_EMBEDDING_CACHE_ENABLED:
        cache_key = hashlib.md5(text.encode()).hexdigest()
        cached = _load_from_cache(cache_key)
        if cached is not None:
            return cached

    # Try OpenAI
    embedding = _get_openai_embedding(text)

    # Fall back to simple vector
    if embedding is None:
        embedding = _simple_text_to_vector(text, TOOLS_EMBEDDING_DIMENSION)

    # Cache result
    if use_cache and TOOLS_EMBEDDING_CACHE_ENABLED:
        _save_to_cache(cache_key, embedding)

    return embedding


def _load_from_cache(key: str) -> Optional[List[float]]:
    """Load embedding from cache."""
    try:
        cache_file = os.path.join(EMBEDDING_CACHE_DIR, f"{key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _save_to_cache(key: str, embedding: List[float]) -> None:
    """Save embedding to cache."""
    try:
        os.makedirs(EMBEDDING_CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(EMBEDDING_CACHE_DIR, f"{key}.json")
        with open(cache_file, "w") as f:
            json.dump(embedding, f)
    except Exception as e:
        log.debug("[B3] Cache save failed: %s", e)


# =============================================================================
# TOOL EMBEDDING GENERATION
# =============================================================================

@lru_cache(maxsize=1)
def get_all_tool_embeddings() -> List[ToolEmbedding]:
    """
    Generate embeddings for all tools in the database.

    Returns cached list of ToolEmbedding objects.
    """
    embeddings = []

    for tool in TOOL_DATABASE:
        text = _get_text_for_embedding(tool)
        embedding = get_embedding(text, use_cache=True)

        tool_embedding = ToolEmbedding(
            tool_name=tool["name"],
            tool_id=tool["id"],
            description=tool.get("description", ""),
            categories=tool.get("categories", []),
            sector_usecases=tool.get("usecases", []),
            embedding=embedding,
            metadata={
                "complexity": tool.get("complexity", "medium"),
                "pricing": tool.get("pricing", "unknown"),
            },
        )
        embeddings.append(tool_embedding)

    log.info("[B3] Generated embeddings for %d tools", len(embeddings))
    return embeddings


def get_tool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get tool from database by name."""
    name_lower = name.lower()
    for tool in TOOL_DATABASE:
        if tool["name"].lower() == name_lower or tool["id"].lower() == name_lower:
            return tool
    return None


def get_tool_embedding_by_name(name: str) -> Optional[ToolEmbedding]:
    """Get tool embedding by name."""
    embeddings = get_all_tool_embeddings()
    name_lower = name.lower()
    for emb in embeddings:
        if emb.tool_name.lower() == name_lower or emb.tool_id.lower() == name_lower:
            return emb
    return None


# =============================================================================
# SEMANTIC SEARCH
# =============================================================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def semantic_search(
    query_embedding: List[float],
    k: int = 10,
    min_similarity: float = 0.0,
) -> List[SemanticSearchResult]:
    """
    Search for tools similar to query embedding.

    Args:
        query_embedding: Query vector
        k: Number of results to return
        min_similarity: Minimum similarity threshold

    Returns:
        List of SemanticSearchResult sorted by similarity
    """
    tool_embeddings = get_all_tool_embeddings()
    clusters = get_tool_clusters()

    # Calculate similarities
    results = []
    for tool_emb in tool_embeddings:
        similarity = cosine_similarity(query_embedding, tool_emb.embedding)

        if similarity >= min_similarity:
            # Find cluster for tool
            cluster_label = ""
            for cluster in clusters:
                if tool_emb.tool_name in cluster.tool_names:
                    cluster_label = cluster.label
                    break

            results.append(SemanticSearchResult(
                tool_name=tool_emb.tool_name,
                tool_id=tool_emb.tool_id,
                similarity_score=similarity,
                categories=tool_emb.categories,
                description=tool_emb.description,
                cluster_label=cluster_label,
            ))

    # Sort by similarity
    results.sort(key=lambda x: x.similarity_score, reverse=True)

    return results[:k]


def semantic_search_for_usecase(
    usecase_text: str,
    k: int = 10,
    branch: str = "",
) -> List[SemanticSearchResult]:
    """
    Search for tools matching a use case description.

    Args:
        usecase_text: Natural language use case description
        k: Number of results to return
        branch: Optional branch for context

    Returns:
        List of matching tools
    """
    # Build query with branch context
    query = usecase_text
    if branch:
        query = f"{branch} industry: {usecase_text}"

    # Get query embedding
    query_embedding = get_embedding(query, use_cache=False)

    # Search
    results = semantic_search(query_embedding, k=k, min_similarity=0.1)

    log.debug(
        "[B3] Semantic search for '%s' found %d tools",
        usecase_text[:50],
        len(results),
    )

    return results


def semantic_search_for_category(
    category: str,
    k: int = 10,
) -> List[SemanticSearchResult]:
    """
    Search for tools in a category.

    Args:
        category: Category name
        k: Number of results to return

    Returns:
        List of matching tools
    """
    query = f"AI tools for {category}"
    query_embedding = get_embedding(query, use_cache=False)
    return semantic_search(query_embedding, k=k, min_similarity=0.1)


# =============================================================================
# CLUSTERING
# =============================================================================

def _assign_tool_to_cluster(tool: Dict[str, Any]) -> int:
    """
    Assign a tool to a cluster based on categories and keywords.

    Uses deterministic rule-based assignment for consistency.
    """
    categories = set(c.lower() for c in tool.get("categories", []))
    usecases = set(u.lower() for u in tool.get("usecases", []))
    description = tool.get("description", "").lower()

    all_text = categories | usecases | set(description.split())

    best_cluster = 0
    best_score = 0

    for cluster_def in CLUSTER_DEFINITIONS:
        score = 0

        # Check category overlap
        cluster_categories = set(c.lower() for c in cluster_def.get("categories", []))
        score += len(categories & cluster_categories) * 3

        # Check keyword overlap
        keywords = set(k.lower() for k in cluster_def.get("keywords", []))
        score += len(all_text & keywords)

        if score > best_score:
            best_score = score
            best_cluster = cluster_def["id"]

    return best_cluster


@lru_cache(maxsize=1)
def get_tool_clusters() -> List[ToolCluster]:
    """
    Get tool clusters.

    Uses deterministic rule-based clustering for consistency.
    """
    clusters = []

    # Initialize clusters from definitions
    cluster_tools: Dict[int, List[str]] = {i: [] for i in range(len(CLUSTER_DEFINITIONS))}

    # Assign tools to clusters
    for tool in TOOL_DATABASE:
        cluster_id = _assign_tool_to_cluster(tool)
        cluster_tools[cluster_id].append(tool["name"])

    # Build cluster objects
    for cluster_def in CLUSTER_DEFINITIONS:
        cluster_id = cluster_def["id"]
        tool_names = cluster_tools.get(cluster_id, [])

        cluster = ToolCluster(
            cluster_id=cluster_id,
            label=cluster_def["label"],
            description=cluster_def["description"],
            tool_names=tool_names,
            keywords=cluster_def["keywords"],
            size=len(tool_names),
            centroid=[],  # Not needed for rule-based clustering
        )
        clusters.append(cluster)

    log.info(
        "[B3] Created %d clusters: %s",
        len(clusters),
        [(c.label, c.size) for c in clusters],
    )

    return clusters


def get_cluster_for_tool(tool_name: str) -> Optional[ToolCluster]:
    """Get the cluster containing a tool."""
    clusters = get_tool_clusters()
    for cluster in clusters:
        if tool_name in cluster.tool_names:
            return cluster
    return None


def get_tools_in_cluster(cluster_label: str) -> List[str]:
    """Get all tools in a cluster by label."""
    clusters = get_tool_clusters()
    for cluster in clusters:
        if cluster.label.lower() == cluster_label.lower():
            return cluster.tool_names
    return []


# =============================================================================
# DISCOVERY API
# =============================================================================

def discover_tools_for_profile(
    branch: str,
    size: str,
    usecases: List[str],
    k: int = 15,
) -> List[SemanticSearchResult]:
    """
    Discover tools for a company profile.

    Args:
        branch: Industry branch
        size: Company size (solo/team/kmu)
        usecases: List of use case descriptions
        k: Number of results to return

    Returns:
        List of recommended tools
    """
    all_results: Dict[str, SemanticSearchResult] = {}

    # Search for each use case
    for usecase in usecases:
        results = semantic_search_for_usecase(usecase, k=k // 2, branch=branch)
        for result in results:
            if result.tool_name not in all_results:
                all_results[result.tool_name] = result
            else:
                # Update with higher score if found again
                if result.similarity_score > all_results[result.tool_name].similarity_score:
                    all_results[result.tool_name] = result

    # Also search for branch-specific tools
    branch_results = semantic_search_for_usecase(
        f"AI tools for {branch} industry",
        k=k // 2,
    )
    for result in branch_results:
        if result.tool_name not in all_results:
            all_results[result.tool_name] = result

    # Sort by score and return top k
    sorted_results = sorted(
        all_results.values(),
        key=lambda x: x.similarity_score,
        reverse=True,
    )

    return sorted_results[:k]


def get_tool_database_stats() -> Dict[str, Any]:
    """Get statistics about the tool database."""
    clusters = get_tool_clusters()

    categories = set()
    for tool in TOOL_DATABASE:
        categories.update(tool.get("categories", []))

    return {
        "total_tools": len(TOOL_DATABASE),
        "total_clusters": len(clusters),
        "cluster_sizes": {c.label: c.size for c in clusters},
        "unique_categories": len(categories),
        "categories": sorted(categories),
        "embedding_dimension": TOOLS_EMBEDDING_DIMENSION,
        "embedding_model": TOOLS_EMBEDDING_MODEL,
    }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[B3] Tools Embedding Engine loaded - %d tools, %d clusters, embedding_dim=%d",
    len(TOOL_DATABASE),
    len(CLUSTER_DEFINITIONS),
    TOOLS_EMBEDDING_DIMENSION,
)
