"""
settings.py – zentrale Konfiguration (Pydantic v2)
--------------------------------------------------
Lädt alle relevanten Umgebungsvariablen und stellt get_settings()
für den einfachen Import bereit.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecurityConfig(BaseModel):
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7
    # Service-Token für headless/automated API-Zugriff (Golden Reports, CI)
    service_token_enabled: bool = False
    service_token_secret: Optional[str] = None

    @field_validator("jwt_secret")
    @classmethod
    def _no_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("JWT_SECRET darf nicht leer sein.")
        return v


class MailConfig(BaseModel):
    provider: str = "resend"  # "resend" | "smtp"
    from_email: Optional[EmailStr] = None
    from_name: str | None = None

    # Global Email Kill-Switch
    disable_emails: bool = False  # DISABLE_EMAILS=1 blocks ALL email sending

    # SMTP
    host: Optional[str] = None
    port: int = 587
    user: Optional[str] = None
    password: Optional[str] = None
    starttls: bool = True
    timeout: int = 30


class ResearchConfig(BaseModel):
    provider: str = "hybrid"  # "tavily" | "perplexity" | "hybrid"
    lang: str = "de-DE"
    country: str = "de"
    cache_path: str = "data/research_cache.json"
    cache_ttl: int = 60 * 60 * 24 * 7  # 7 Tage
    include_tools: str | None = None
    include_funding: str | None = None
    exclude_domains: str | None = None
    days_default: int = 30
    days_min: int = 7
    days_max: int = 60


class RateLimitConfig(BaseModel):
    window_sec: int = 300
    max_login: int = 5
    max_request_code: int = 10


class OpenAIConfig(BaseModel):
    api_key: Optional[str] = None
    model: str = "gpt-4o"
    temperature: float = 0.2
    max_completion_tokens: int = 3000
    timeout: int = 90  # SPRINT G13-D: reduced from 120s for faster fallback triggering
    gamechanger_temperature: float = 0.4

    # ---------------------------------------------------------------------------
    # GPT-5.2 Migration: Model Routing Scaffolding
    # ---------------------------------------------------------------------------
    # PHASE 0/1 (SCAFFOLDING): Safe defaults - no behavior change until ENV set.
    # PHASE 2 (ENABLE): Set via Railway ENV to activate GPT-5.2.
    #
    # FAST: Quick tasks, HTML snippets, format generation
    model_fast: str = "gpt-4o"  # Phase 0/1: safe default (uses current model)
    # REASONING: Complex tasks (Consistency, Governance, Auto-Heal)
    model_reasoning: str = "gpt-4o"  # Phase 0/1: safe default (uses current model)
    # FALLBACK: Stable fallback model when primary fails (keep stable, not 5.2)
    model_fallback: str = "gpt-4o-mini"  # Stable fallback
    # Reasoning effort for reasoning model (low/medium/high, xhigh selectively)
    reasoning_effort: str = "high"

    @property
    def max_tokens(self) -> int:
        """Backwards-kompatibler Alias für max_completion_tokens"""
        return self.max_completion_tokens


class PerplexityConfig(BaseModel):
    api_key: Optional[str] = None
    model: str = "sonar-pro"
    max_tokens: int = 1200
    timeout_ms: int = 15000
    search_depth: str = "advanced"


class TavilyConfig(BaseModel):
    api_key: Optional[str] = None
    timeout_ms: int = 15000
    max_results: int = 8


class PDFConfig(BaseModel):
    service_url: str = ""
    timeout_ms: int = 120000  # optimiert: 120s statt 90s
    template_path: str = "templates/pdf_template.html"
    max_html_kb: int = 350
    max_pdf_mb: int = 20
    warn_size_mb: float = 10.0
    alert_size_mb: float = 18.0


class MonitoringConfig(BaseModel):
    """Monitoring & Alerting Configuration."""
    admin_notify_email: Optional[str] = None
    admin_feedback_email: Optional[str] = None
    min_section_words: int = 50
    max_fallbacks_per_report: int = 3
    guardrail_high_conf: float = 0.9
    token_budget_threshold_pct: float = 95.0
    pdf_timeout_sec: float = 20.0
    # SPRINT G13-D: Fallback optimization settings
    fallback_token_budget: int = 2500  # max tokens for fallback content generation
    aggressive_timeout_sec: int = 60  # timeout for non-critical sections


class AppSettings(BaseSettings):
    # Meta
    app_name: str = "KI Status Report API"
    env: str = "production"
    log_level: str = "info"

    # URLs
    site_url: str = "https://ki-sicherheit.jetzt"
    backend_base: str = ""

    # DB/Cache
    database_url: str
    redis_url: Optional[str] = None

    # CORS
    cors_allow_any: bool = False
    cors_origins: List[str] = []

    # Feature-Flags (nur passende Auswahl)
    enable_llm_cache: bool = True
    enable_perplexity: bool = True
    enable_quality_gates: bool = True
    enable_realistic_scores: bool = True
    enable_ai_act_section: bool = True
    enable_ai_act_table: bool = True
    enable_admin_notify: bool = True
    enable_repair_html: bool = True

    # E-Mail/Resend/SMTP
    mail: MailConfig = MailConfig()

    # Security / JWT
    security: SecurityConfig

    # OpenAI/Perplexity/Tavily
    openai: OpenAIConfig = OpenAIConfig()
    perplexity: PerplexityConfig = PerplexityConfig()
    tavily: TavilyConfig = TavilyConfig()

    # Research
    research: ResearchConfig = ResearchConfig()

    # Rate-Limit
    rate: RateLimitConfig = RateLimitConfig()

    # PDF
    pdf: PDFConfig = PDFConfig()

    # Monitoring
    monitoring: MonitoringConfig = MonitoringConfig()

    # Report-/Content-Pfade
    benchmarks_path: str = "data/benchmarks.json"
    starter_stacks_path: str = "data/starter_stacks.json"
    ai_act_info_path: str = "EU-AI-ACT-Infos-wichtig.txt"
    report_date: bool = True

    model_config = SettingsConfigDict(
        env_prefix="", 
        case_sensitive=False, 
        extra="ignore",
        # Deaktiviere automatisches ENV-Loading - wir nutzen from_env()
        env_ignore_empty=True,
        env_parse_none_str="null"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_csv(cls, v):
        # Wenn v None oder leer ist, gib leere Liste zurück
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @classmethod
    def from_env(cls) -> "AppSettings":
        # Konstruktor mit verschachtelten Sektionen aus ENV befüllen
        import os

        def get_bool(name: str, default: bool = False) -> bool:
            val = os.getenv(name, str(int(default)))
            return val in ("1", "true", "True", "yes", "on")

        def get_list(name: str, default: str = "") -> list:
            """Konvertiere CSV-String aus ENV in Liste"""
            val = os.getenv(name, default)
            if not val:
                return []
            return [s.strip() for s in val.split(",") if s.strip()]

        # Verwende model_construct um automatisches ENV-Loading zu umgehen
        s = cls.model_construct(
            app_name=os.getenv("APP_NAME", "KI Status Report API"),
            env=os.getenv("ENV", "production"),
            log_level=os.getenv("LOG_LEVEL", "info"),
            site_url=os.getenv("SITE_URL", "https://ki-sicherheit.jetzt"),
            backend_base=os.getenv("BACKEND_BASE", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            redis_url=os.getenv("REDIS_URL"),
            cors_allow_any=get_bool("CORS_ALLOW_ANY", False),
            cors_origins=get_list("CORS_ORIGINS"),
            enable_llm_cache=get_bool("ENABLE_LLM_CACHE", True),
            enable_perplexity=get_bool("ENABLE_PERPLEXITY", True),
            enable_quality_gates=get_bool("ENABLE_QUALITY_GATES", True),
            enable_realistic_scores=get_bool("ENABLE_REALISTIC_SCORES", True),
            enable_ai_act_section=get_bool("ENABLE_AI_ACT_SECTION", True),
            enable_ai_act_table=get_bool("ENABLE_AI_ACT_TABLE", True),
            enable_admin_notify=get_bool("ENABLE_ADMIN_NOTIFY", True),
            enable_repair_html=get_bool("ENABLE_REPAIR_HTML", True),
            mail=MailConfig(
                provider=os.getenv("EMAIL_PROVIDER", "resend"),
                from_email=os.getenv("RESEND_FROM") or os.getenv("SMTP_FROM"),
                from_name=os.getenv("SMTP_FROM_NAME") or "KI‑Sicherheit.jetzt",
                disable_emails=get_bool("DISABLE_EMAILS", False),
                host=os.getenv("SMTP_HOST"),
                port=int(os.getenv("SMTP_PORT", "587")),
                user=os.getenv("SMTP_USER"),
                password=os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS"),
                starttls=get_bool("SMTP_STARTTLS", True),
                timeout=int(os.getenv("SMTP_TIMEOUT", "30")),
            ),
            security=SecurityConfig(
                jwt_secret=os.getenv("JWT_SECRET", ""),
                jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
                jwt_expire_days=int(os.getenv("JWT_EXPIRE_DAYS", "7")),
                service_token_enabled=get_bool("SERVICE_TOKEN_ENABLED", False),
                service_token_secret=os.getenv("SERVICE_TOKEN_SECRET"),
            ),
            openai=OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
                max_completion_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "3000")),
                timeout=int(os.getenv("OPENAI_TIMEOUT", "120")),
                gamechanger_temperature=float(os.getenv("OPENAI_TEMP_GAMECHANGER", "0.4")),
                # GPT-5.2 Migration: Model Routing
                model_fast=os.getenv("OPENAI_MODEL_FAST", os.getenv("OPENAI_MODEL", "gpt-4o")),
                model_reasoning=os.getenv("OPENAI_MODEL_REASONING", os.getenv("OPENAI_MODEL", "gpt-4o")),
                model_fallback=os.getenv("OPENAI_MODEL_FALLBACK", "gpt-4o-mini"),
                reasoning_effort=os.getenv("OPENAI_REASONING_EFFORT", "high"),
            ),
            perplexity=PerplexityConfig(
                api_key=os.getenv("PERPLEXITY_API_KEY"),
                model=os.getenv("PERPLEXITY_MODEL", "sonar-pro"),
                max_tokens=int(os.getenv("PERPLEXITY_MAX_TOKENS", "1200")),
                timeout_ms=int(os.getenv("PERPLEXITY_TIMEOUT_MS", "15000")),
                search_depth=os.getenv("PERPLEXITY_SEARCH_DEPTH", "advanced"),
            ),
            tavily=TavilyConfig(
                api_key=os.getenv("TAVILY_API_KEY"),
                timeout_ms=int(os.getenv("TAVILY_TIMEOUT_MS", "15000")),
                max_results=int(os.getenv("TAVILY_MAX_RESULTS", "8")),
            ),
            research=ResearchConfig(
                provider=os.getenv("RESEARCH_PROVIDER", "hybrid"),
                lang=os.getenv("RESEARCH_LANG", "de-DE"),
                country=os.getenv("RESEARCH_COUNTRY", "de"),
                cache_path=os.getenv("RESEARCH_CACHE_PATH", "data/research_cache.json"),
                cache_ttl=int(os.getenv("RESEARCH_CACHE_TTL", str(60*60*24*7))),
                include_tools=os.getenv("RESEARCH_INCLUDE_TOOLS"),
                include_funding=os.getenv("RESEARCH_INCLUDE_FUNDING"),
                exclude_domains=os.getenv("RESEARCH_EXCLUDE"),
                days_default=int(os.getenv("RESEARCH_DAYS_DEFAULT", "30")),
                days_min=int(os.getenv("RESEARCH_DAYS_MIN", "7")),
                days_max=int(os.getenv("RESEARCH_DAYS_MAX", "60")),
            ),
            rate=RateLimitConfig(
                window_sec=int(os.getenv("AUTH_RATE_WINDOW_SEC", "300")),
                max_login=int(os.getenv("AUTH_RATE_MAX_LOGIN", "5")),
                max_request_code=int(os.getenv("AUTH_RATE_MAX_REQUEST_CODE", "10")),
            ),
            pdf=PDFConfig(
                service_url=os.getenv("PDF_SERVICE_URL", ""),
                timeout_ms=int(os.getenv("PDF_TIMEOUT_MS", "120000")),
                template_path=os.getenv("REPORT_TEMPLATE_PATH", "templates/pdf_template_v7.html"),
                max_html_kb=int(os.getenv("MAX_HTML_PAYLOAD_KB", "350")),
                max_pdf_mb=int(os.getenv("MAX_PDF_SIZE_MB", "20")),
                warn_size_mb=float(os.getenv("PDF_WARN_SIZE_MB", "10")),
                alert_size_mb=float(os.getenv("PDF_ALERT_SIZE_MB", "18")),
            ),
            monitoring=MonitoringConfig(
                admin_notify_email=os.getenv("ADMIN_NOTIFY_EMAIL"),
                admin_feedback_email=os.getenv("ADMIN_FEEDBACK_EMAIL"),
                min_section_words=int(os.getenv("MIN_SECTION_WORDS", "50")),
                max_fallbacks_per_report=int(os.getenv("MAX_FALLBACKS_PER_REPORT", "3")),
                guardrail_high_conf=float(os.getenv("GUARDRAIL_HIGH_CONF", "0.9")),
                token_budget_threshold_pct=float(os.getenv("TOKEN_BUDGET_THRESHOLD_PCT", "95")),
                pdf_timeout_sec=float(os.getenv("PDF_TIMEOUT_SEC", "20")),
            ),
            benchmarks_path=os.getenv("BENCHMARKS_PATH", "data/benchmarks.json"),
            starter_stacks_path=os.getenv("STARTER_STACKS_PATH", "data/starter_stacks.json"),
            ai_act_info_path=os.getenv("AI_ACT_INFO_PATH", "EU-AI-ACT-Infos-wichtig.txt"),
            report_date=os.getenv("REPORT_DATE", "1") in ("1","true","True"),
        )
        # Cast to AppSettings to satisfy mypy
        validated: AppSettings = cls.model_validate(s)
        return validated


@lru_cache
def get_settings() -> AppSettings:
    s = AppSettings.from_env()
    # Explizite Validierung nach model_construct
    if not s.security.jwt_secret:
        raise ValueError("JWT_SECRET muss gesetzt sein! Bitte setzen Sie die Umgebungsvariable JWT_SECRET.")
    if not s.database_url:
        raise ValueError("DATABASE_URL muss gesetzt sein! Bitte setzen Sie die Umgebungsvariable DATABASE_URL.")
    return s


# Singleton-Instanz für direkten Import (z.B. "from settings import settings")
settings = get_settings()