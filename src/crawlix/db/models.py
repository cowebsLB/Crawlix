"""SQLAlchemy models — mirrors product plan table dictionary."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    default_domain: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    locations: Mapped[list[Location]] = relationship(back_populates="project")
    keywords: Mapped[list[Keyword]] = relationship(back_populates="project")
    pages: Mapped[list[Page]] = relationship(back_populates="project")
    jobs: Mapped[list[Job]] = relationship(back_populates="project")
    competitor_targets: Mapped[list[CompetitorTarget]] = relationship(back_populates="project")
    integration_accounts: Mapped[list[IntegrationAccount]] = relationship(back_populates="project")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    business_name: Mapped[str] = mapped_column(String(512), nullable=False)
    address_line1: Mapped[str | None] = mapped_column(String(512), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(512), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    primary_phone_e164: Mapped[str | None] = mapped_column(String(32), nullable=True)
    primary_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="locations")
    citation_checks: Mapped[list[CitationCheck]] = relationship(back_populates="location")


class Keyword(Base):
    __tablename__ = "keywords"
    __table_args__ = (Index("ix_keywords_project_archived", "project_id", "archived_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    phrase: Mapped[str] = mapped_column(String(512), nullable=False)
    locale: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tags_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship(back_populates="keywords")
    serp_results: Mapped[list[SerpResult]] = relationship(back_populates="keyword")
    rankings: Mapped[list[Ranking]] = relationship(back_populates="keyword")


class SerpResult(Base):
    __tablename__ = "serp_results"
    __table_args__ = (Index("ix_serp_keyword_fetched", "keyword_id", "fetched_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id", ondelete="CASCADE"), index=True)
    search_engine: Mapped[str] = mapped_column(String(64), nullable=False)
    geo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device: Mapped[str | None] = mapped_column(String(32), nullable=True)
    results_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    html_gzip: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    parser_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(32), default="ok")

    keyword: Mapped[Keyword] = relationship(back_populates="serp_results")
    rankings: Mapped[list[Ranking]] = relationship(back_populates="serp_result")


class Ranking(Base):
    __tablename__ = "rankings"
    __table_args__ = (Index("ix_rankings_keyword_tracked", "keyword_id", "tracked_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id", ondelete="CASCADE"), index=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matched_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    search_engine: Mapped[str] = mapped_column(String(64), nullable=False)
    geo_location_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device: Mapped[str | None] = mapped_column(String(32), nullable=True)
    serp_result_id: Mapped[int | None] = mapped_column(
        ForeignKey("serp_results.id", ondelete="SET NULL"), nullable=True, index=True
    )
    provenance: Mapped[str] = mapped_column(
        String(32), nullable=False, default="automated_serp"
    )  # automated_serp | manual_html_import | api
    tracked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    degraded: Mapped[bool] = mapped_column(Boolean, default=False)

    keyword: Mapped[Keyword] = relationship(back_populates="rankings")
    serp_result: Mapped[SerpResult | None] = relationship(back_populates="rankings")


class Page(Base):
    __tablename__ = "pages"
    __table_args__ = (
        UniqueConstraint("project_id", "url_norm", name="uq_pages_project_url"),
        Index("ix_pages_project_last_crawled", "project_id", "last_crawled_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    url_norm: Mapped[str] = mapped_column(String(2048), nullable=False)
    url_final: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    crawl_job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    crawl_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)

    project: Mapped[Project] = relationship(back_populates="pages")
    crawled_data: Mapped[list[CrawledData]] = relationship(back_populates="page")
    page_links: Mapped[list[PageLink]] = relationship(
        back_populates="from_page", foreign_keys="PageLink.from_page_id"
    )
    seo_audits: Mapped[list[SeoAudit]] = relationship(back_populates="page")


class CrawledData(Base):
    __tablename__ = "crawled_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    html_gzip: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    headers_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    bytes_raw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    page: Mapped[Page] = relationship(back_populates="crawled_data")


class PageLink(Base):
    __tablename__ = "page_links"
    __table_args__ = (
        Index("ix_page_links_from", "from_page_id"),
        Index("ix_page_links_to", "to_url_norm"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_page_id: Mapped[int] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), index=True)
    to_url_norm: Mapped[str] = mapped_column(String(2048), nullable=False)
    link_text: Mapped[str | None] = mapped_column(String(512), nullable=True)
    nofollow: Mapped[bool] = mapped_column(Boolean, default=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)

    from_page: Mapped[Page] = relationship(
        back_populates="page_links", foreign_keys=[from_page_id]
    )


class SeoAudit(Base):
    __tablename__ = "seo_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    category_scores_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    issues_json: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    recommendations_json: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    audited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    page: Mapped[Page] = relationship(back_populates="seo_audits")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_project_status_created", "project_id", "status", "created_at"),
        Index("ix_jobs_type_status", "type", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    result_summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped[Project] = relationship(back_populates="jobs")
    crawl_queue_items: Mapped[list[CrawlQueueItem]] = relationship(back_populates="job")


class CrawlQueueItem(Base):
    __tablename__ = "crawl_queue_items"
    __table_args__ = (
        Index("ix_crawl_queue_job_state", "job_id", "state"),
        Index("ix_crawl_queue_url", "url_norm"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    url_norm: Mapped[str] = mapped_column(String(2048), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[str] = mapped_column(String(32), default="pending")
    parent_page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id", ondelete="SET NULL"), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    job: Mapped[Job] = relationship(back_populates="crawl_queue_items")


class CitationSource(Base):
    __tablename__ = "citation_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_url: Mapped[str] = mapped_column(Text, nullable=False)
    region_tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    requires_playwright: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    pack_version: Mapped[int] = mapped_column(Integer, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    checks: Mapped[list[CitationCheck]] = relationship(back_populates="source")


class CitationCheck(Base):
    __tablename__ = "citation_checks"
    __table_args__ = (Index("ix_citation_checks_loc_src", "location_id", "source_id", "fetched_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("citation_sources.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    requested_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scores_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    response_html_gzip: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    playwright_used: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="ok")
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    location: Mapped[Location] = relationship(back_populates="citation_checks")
    source: Mapped[CitationSource] = relationship(back_populates="checks")


class Proxy(Base):
    __tablename__ = "proxies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    proxy_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_secret: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    health_state: Mapped[str] = mapped_column(String(32), default="healthy")
    cooldown_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(32), default="str")


class AiCache(Base):
    __tablename__ = "ai_cache"
    __table_args__ = (
        UniqueConstraint("prompt_hash", "model", name="uq_ai_cache_prompt_model"),
        Index("ix_ai_cache_expires", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IntegrationAccount(Base):
    __tablename__ = "integration_accounts"
    __table_args__ = (Index("ix_integration_project_provider", "project_id", "provider"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    account_label: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_tokens_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship(back_populates="integration_accounts")


class CompetitorTarget(Base):
    __tablename__ = "competitor_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="competitor_targets")
