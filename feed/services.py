import html
import json
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F, QuerySet
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError

from .models import DailyPoll, PollOption, TenantArticle, TenantPortal

HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(raw: str, max_len: int = 260) -> str:
    clean = html.unescape(HTML_TAG_RE.sub(" ", raw or ""))
    clean = " ".join(clean.split()).strip()
    if len(clean) > max_len:
        return clean[: max_len - 1].rstrip() + "…"
    return clean


def map_category_to_topic(raw_name: str) -> str:
    text = (raw_name or "").lower()
    if any(k in text for k in ("econ", "biz", "busi", "bank", "market", "অর্থ", "বাণিজ্য")):
        return TenantArticle.Topic.ECONOMY
    if any(k in text for k in ("sport", "cricket", "football", "খেলা", "ক্রিকেট")):
        return TenantArticle.Topic.SPORTS
    if any(k in text for k in ("tech", "ai", "science", "প্রযুক্তি", "বিজ্ঞান")):
        return TenantArticle.Topic.TECH
    if any(k in text for k in ("job", "career", "edu", "চাকরি", "শিক্ষা")):
        return TenantArticle.Topic.JOBS
    if any(k in text for k in ("world", "inter", "global", "আন্তর্জাতিক", "বিশ্ব")):
        return TenantArticle.Topic.WORLD
    return TenantArticle.Topic.NATIONAL


def parse_timestamp(raw: str | None):
    if not raw:
        return timezone.now()
    parsed = parse_datetime(raw)
    if not parsed:
        return timezone.now()
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def list_trending_articles(limit: int = 15, max_per_portal: int = 2) -> list[TenantArticle]:
    """Return latest breaking/recent articles ONLY from active TenantPortals with a fair cap per portal."""
    candidates = (
        TenantArticle.objects.select_related("portal")
        .filter(is_active=True, portal__is_active=True)
        .order_by("-is_breaking", "-published_at", "-id")[: limit * 4]
    )
    selected: list[TenantArticle] = []
    counts_by_portal: dict[int, int] = {}
    for article in candidates:
        used = counts_by_portal.get(article.portal_id, 0)
        if used >= max_per_portal:
            continue
        selected.append(article)
        counts_by_portal[article.portal_id] = used + 1
        if len(selected) >= limit:
            break
    return selected


def ingest_tenant_article(validated_data: dict) -> tuple[TenantArticle, bool]:
    """Auto-register/update the TenantPortal and upsert the pushed TenantArticle."""
    slug = validated_data["portal_slug"].strip()
    domain = validated_data["portal_domain"].strip().lower()
    name = validated_data["portal_name"].strip()
    logo_url = (validated_data.get("portal_logo_url") or "").strip()

    with transaction.atomic():
        portal, created_portal = TenantPortal.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "domain": domain,
                "logo_url": logo_url,
                "source_type": TenantPortal.SourceType.NEWSPAPER_API,
                "is_active": True,
            },
        )
        if not created_portal:
            changed = []
            if name and portal.name != name:
                portal.name = name
                changed.append("name")
            if logo_url and portal.logo_url != logo_url:
                portal.logo_url = logo_url
                changed.append("logo_url")
            portal.last_synced_at = timezone.now()
            changed.extend(["last_synced_at", "updated_at"])
            portal.save(update_fields=changed)

        article, was_created = upsert_tenant_article(
            portal,
            {
                "external_id": validated_data["external_id"],
                "title": validated_data["title"].strip(),
                "summary": strip_html(validated_data.get("summary") or validated_data["title"]),
                "topic": map_category_to_topic(validated_data.get("topic", "")),
                "article_url": validated_data["article_url"].strip(),
                "image_url": (validated_data.get("image_url") or "").strip(),
                "is_breaking": bool(validated_data.get("is_breaking", False)),
                "published_at": parse_timestamp(validated_data.get("published_at")),
            },
        )
    return article, was_created


def list_feed_articles(topic: str | None = None, limit: int = 30) -> QuerySet[TenantArticle]:
    """Return latest feed stories ONLY from active TenantPortals."""
    qs = (
        TenantArticle.objects.select_related("portal")
        .filter(is_active=True, portal__is_active=True)
        .order_by("-published_at", "-id")
    )
    if topic and topic != "All":
        qs = qs.filter(topic__iexact=topic.strip())
    return qs[:limit]


def get_active_poll() -> DailyPoll | None:
    return (
        DailyPoll.objects.prefetch_related("options")
        .filter(is_active=True)
        .order_by("-created_at")
        .first()
    )


def record_poll_vote(poll_id: int, option_id: int) -> DailyPoll:
    with transaction.atomic():
        poll = DailyPoll.objects.filter(pk=poll_id, is_active=True).first()
        if not poll:
            raise ValidationError({"poll": "Active poll not found."})

        updated = PollOption.objects.filter(pk=option_id, poll=poll).update(votes=F("votes") + 1)
        if updated == 0:
            raise ValidationError({"optionId": "Poll option does not belong to this poll."})

    return DailyPoll.objects.prefetch_related("options").get(pk=poll_id)


def fetch_json_url(url: str, headers: dict | None = None, timeout: int = 10):
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "BDNewsLiveBot/1.0", **(headers or {})})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def upsert_tenant_article(portal: TenantPortal, payload: dict) -> tuple[TenantArticle, bool]:
    try:
        return TenantArticle.objects.update_or_create(
            portal=portal,
            external_id=str(payload["external_id"]),
            defaults={
                "title": payload["title"][:300],
                "summary": payload.get("summary", ""),
                "topic": payload.get("topic", TenantArticle.Topic.NATIONAL),
                "article_url": payload["article_url"][:1000],
                "image_url": (payload.get("image_url") or "")[:1000],
                "is_breaking": bool(payload.get("is_breaking", False)),
                "published_at": payload.get("published_at") or timezone.now(),
                "is_active": True,
            },
        )
    except IntegrityError as exc:
        raise ValidationError({"article": f"Database constraint error: {exc}"})


def sync_portal_articles(portal: TenantPortal, limit: int = 15) -> dict:
    """Sync published public articles for a single TenantPortal."""
    created = 0
    updated = 0

    if portal.source_type == TenantPortal.SourceType.NEWSPAPER_API:
        base_url = (portal.api_base_url or settings.NEWSPAPER_API_BASE_URL).rstrip("/")
        endpoint = f"{base_url}/api/news/articles/"
        data = fetch_json_url(endpoint, headers={"X-Tenant-Slug": portal.slug})
        records = data if isinstance(data, list) else data.get("results", [])

        for row in records[:limit]:
            if row.get("is_internal") or row.get("status") != "PUBLISHED":
                continue
            slug = row.get("slug", "")
            article_url = portal.article_url_template.format(domain=portal.domain, slug=slug)
            category_obj = row.get("category") or {}
            category_name = category_obj.get("name", "") if isinstance(category_obj, dict) else ""
            summary = strip_html(row.get("ai_summary") or row.get("title", ""))

            _, was_created = upsert_tenant_article(
                portal,
                {
                    "external_id": str(row.get("id") or slug),
                    "title": row.get("title", "").strip(),
                    "summary": summary,
                    "topic": map_category_to_topic(category_name),
                    "article_url": article_url,
                    "image_url": row.get("featured_image_url") or "",
                    "is_breaking": bool(row.get("is_breaking", False)),
                    "published_at": parse_timestamp(row.get("published_at") or row.get("created_at")),
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

    elif portal.source_type == TenantPortal.SourceType.WORDPRESS_API:
        base_url = (portal.api_base_url or f"https://{portal.domain}").rstrip("/")
        endpoint = f"{base_url}/wp-json/wp/v2/posts?_embed&per_page={limit}"
        records = fetch_json_url(endpoint)
        if not isinstance(records, list):
            records = []

        for row in records[:limit]:
            title = strip_html((row.get("title") or {}).get("rendered", ""), max_len=300)
            excerpt = strip_html((row.get("excerpt") or {}).get("rendered", ""), max_len=260)
            link = row.get("link") or f"https://{portal.domain}"
            image_url = ""
            embedded = row.get("_embedded") or {}
            media = embedded.get("wp:featuredmedia") or []
            if media and isinstance(media, list) and isinstance(media[0], dict):
                image_url = media[0].get("source_url") or ""

            _, was_created = upsert_tenant_article(
                portal,
                {
                    "external_id": str(row.get("id")),
                    "title": title,
                    "summary": excerpt or title,
                    "topic": TenantArticle.Topic.NATIONAL,
                    "article_url": link,
                    "image_url": image_url,
                    "is_breaking": False,
                    "published_at": parse_timestamp(row.get("date_gmt") or row.get("date")),
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

    portal.last_synced_at = timezone.now()
    portal.save(update_fields=["last_synced_at", "updated_at"])
    return {"portal": portal.slug, "created": created, "updated": updated}


def sync_all_active_portals(limit_per_portal: int = 15) -> dict:
    portals = TenantPortal.objects.filter(is_active=True)
    results = []
    errors = []
    for portal in portals:
        try:
            results.append(sync_portal_articles(portal, limit=limit_per_portal))
        except (URLError, TimeoutError, ValueError, OSError) as exc:
            errors.append({"portal": portal.slug, "error": str(exc)})
    return {"synced": results, "errors": errors}


def seed_default_poll() -> DailyPoll:
    existing = DailyPoll.objects.filter(is_active=True).first()
    if existing:
        return existing

    poll = DailyPoll.objects.create(
        question="আজকের সবচেয়ে গুরুত্বপূর্ণ খবর কোন বিষয়ে পড়তে চান?",
        is_active=True,
    )
    options = [
        ("জাতীয় ও রাজনীতি (National)", 1),
        ("অর্থনীতি ও বাজারদর (Economy)", 2),
        ("চাকরি ও শিক্ষা (Jobs & Edu)", 3),
        ("খেলাধুলা ও টেক (Sports & Tech)", 4),
    ]
    PollOption.objects.bulk_create(
        [PollOption(poll=poll, label=label, sort_order=order) for label, order in options]
    )
    return poll
