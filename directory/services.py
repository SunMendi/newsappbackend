from django.db import IntegrityError
from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from .models import Newspaper


DEFAULT_NEWSPAPERS_SEED = [
    # BANGLA
    ("bn-amardesh", "Daily Amardesh", "আমার দেশ", "https://www.dailyamardesh.com", "BANGLA", "#B91C1C", "National Bangla Daily", 1),
    ("bn-jugantor", "Jugantor", "যুগান্তর", "https://www.jugantor.com", "BANGLA", "#1E293B", "National Bangla Daily", 2),
    ("bn-ittefaq", "Ittefaq", "দৈনিক ইত্তেফাক", "https://www.ittefaq.com.bd", "BANGLA", "#0F172A", "Since 1953", 3),
    ("bn-amadershomoy", "Dainik Amader Shomoy", "আমাদের সময়", "https://www.dainikamadershomoy.com", "BANGLA", "#15803D", "National Bangla Daily", 4),
    ("bn-kalerkantho", "Kalerkantho", "কালের কণ্ঠ", "https://www.kalerkantho.com", "BANGLA", "#111827", "National Bangla Daily", 5),
    ("bn-nayadiganta", "Nayadiganta", "নয়া দিগন্ত", "https://www.dailynayadiganta.com", "BANGLA", "#D97706", "National Bangla Daily", 6),
    ("bn-inqilab", "Inqilab", "দৈনিক ইনকিলাব", "https://dailyinqilab.com", "BANGLA", "#166534", "The Daily Inqilab", 7),
    ("bn-samakal", "Samakal", "সমকাল", "https://samakal.com", "BANGLA", "#1E293B", "National Bangla Daily", 8),
    ("bn-prothomalo", "Prothom Alo", "প্রথম আলো", "https://www.prothomalo.com", "BANGLA", "#DC2626", "Bangladesh Leading Daily", 9),
    ("bn-janakantha", "Janakantha", "দৈনিক জনকণ্ঠ", "https://www.dailyjanakantha.com", "BANGLA", "#B91C1C", "National Bangla Daily", 10),
    ("bn-manobzamin", "Manob Zamin", "মানবজমিন", "https://mzamin.com", "BANGLA", "#DC2626", "Tabloid Daily", 11),
    ("bn-bdpratidin", "Bangladesh Pratidin", "বাংলাদেশ প্রতিদিন", "https://www.bd-pratidin.com", "BANGLA", "#991B1B", "Most Circulated Daily", 12),
    ("bn-kalbela", "Kalbela", "কালবেলা", "https://www.kalbela.com", "BANGLA", "#BE123C", "National Bangla Daily", 13),
    # ENGLISH
    ("en-newage", "New Age", "", "https://www.newagebd.net", "ENGLISH", "#DC2626", "Outspoken Daily", 20),
    ("en-dailysun", "Daily Sun", "", "https://www.daily-sun.com", "ENGLISH", "#EA580C", "True and Impartial", 21),
    ("en-observer", "Daily Observer", "", "https://www.observerbd.com", "ENGLISH", "#0284C7", "Bangladesh English Daily", 22),
    ("en-dhakatribune", "Dhaka Tribune", "", "https://www.dhakatribune.com", "ENGLISH", "#DC2626", "English Daily", 23),
    ("en-financialexpress", "Financial Express", "", "https://thefinancialexpress.com.bd", "ENGLISH", "#1E3A8A", "Finance & Economy", 24),
    ("en-bangladeshtoday", "Bangladesh Today", "", "https://thebangladeshtoday.com", "ENGLISH", "#B91C1C", "English Daily", 25),
    ("en-dailystar", "The Daily Star", "", "https://www.thedailystar.net", "ENGLISH", "#0F172A", "Journalism Without Fear or Favour", 26),
    ("en-unb", "United News of Bangladesh", "", "https://unb.com.bd", "ENGLISH", "#DC2626", "UNB Wire Service", 27),
    ("en-newnation", "The New Nation", "", "https://thedailynewnation.com", "ENGLISH", "#1E3A5F", "Independent English Daily", 28),
    ("en-bdnews24", "BD News24", "", "https://bdnews24.com", "ENGLISH", "#E11D48", "24/7 English Portal", 29),
    ("en-asianage", "The Asian Age", "", "https://dailyasianage.com", "ENGLISH", "#0D9488", "English Daily", 30),
    # INTERNATIONAL
    ("int-telegraph", "The Telegraph", "", "https://www.telegraph.co.uk", "INTERNATIONAL", "#0F172A", "UK National News", 40),
    ("int-guardian", "The Guardian", "", "https://www.theguardian.com", "INTERNATIONAL", "#052962", "Global Journalism", 41),
    ("int-aljazeera", "Al Jazeera", "", "https://www.aljazeera.com", "INTERNATIONAL", "#D97706", "World Breaking News", 42),
    ("int-usatoday", "USA Today", "", "https://www.usatoday.com", "INTERNATIONAL", "#0284C7", "US News Network", 43),
    ("int-bbc", "BBC News", "", "https://www.bbc.com/news", "INTERNATIONAL", "#B91C1C", "World Service & Bangla", 44),
    ("int-cnn", "CNN", "", "https://edition.cnn.com", "INTERNATIONAL", "#CC0000", "International News", 45),
    ("int-dailymail", "Daily Mail", "", "https://www.dailymail.co.uk", "INTERNATIONAL", "#1E40AF", "MailOnline", 46),
    ("int-mirror", "Mirror", "", "https://www.mirror.co.uk", "INTERNATIONAL", "#DC2626", "UK News & Sport", 47),
    ("int-toi", "Times of India", "", "https://timesofindia.indiatimes.com", "INTERNATIONAL", "#111827", "South Asia News", 48),
    ("int-dw", "DW News", "", "https://www.dw.com/bn", "INTERNATIONAL", "#0369A1", "Deutsche Welle Bangla", 49),
    # TV NEWS
    ("tv-somoy", "Somoy News", "সময় টিভি", "https://www.somoynews.tv", "TV NEWS", "#DC2626", "24/7 TV News", 60),
    ("tv-jamuna", "Jamuna TV", "যমুনা টিভি", "https://jamuna.tv", "TV NEWS", "#0284C7", "Live Television News", 61),
    ("tv-channel24", "Channel 24", "চ্যানেল ২৪", "https://www.channel24bd.tv", "TV NEWS", "#EA580C", "Bangladesh News TV", 62),
    ("tv-independent", "Independent TV", "ইনডিপেনডেন্ট টিভি", "https://www.itvbd.com", "TV NEWS", "#1D4ED8", "TV News Portal", 63),
    ("tv-ntv", "NTV Online", "এনটিভি", "https://www.ntvbd.com", "TV NEWS", "#0F766E", "News & Entertainment", 64),
    # BUSINESS
    ("biz-tbs", "The Business Standard", "", "https://www.tbsnews.net", "BUSINESS", "#1D4ED8", "Business & Economy", 70),
    ("biz-bonikbarta", "Bonik Barta", "বণিক বার্তা", "https://bonikbarta.com", "BUSINESS", "#0F766E", "Bangla Business Daily", 71),
    ("biz-sharebiz", "Share Biz", "শেয়ার বিজ", "https://sharebiz.net", "BUSINESS", "#15803D", "Capital Market News", 72),
    ("biz-arthosuchak", "Arthosuchak", "অর্থসূচক", "https://www.arthosuchak.com", "BUSINESS", "#B45309", "Business & Banking", 73),
    # ONLINE
    ("on-jagonews", "Jago News 24", "জাগো নিউজ ২৪", "https://www.jagonews24.com", "ONLINE", "#15803D", "Online News Portal", 80),
    ("on-dhakapost", "Dhaka Post", "ঢাকা পোস্ট", "https://www.dhakapost.com", "ONLINE", "#0369A1", "Online News Portal", 81),
    ("on-banglatribune", "Bangla Tribune", "বাংলা ট্রিবিউন", "https://www.banglatribune.com", "ONLINE", "#B91C1C", "Online Bangla Portal", 82),
    ("on-banglanews24", "Banglanews24", "বাংলানিউজ২৪", "https://www.banglanews24.com", "ONLINE", "#0D9488", "24/7 Online Portal", 83),
    ("on-bdjobs", "BDJobs Circulars", "চাকরির খবর", "https://www.bdjobs.com", "ONLINE", "#1D4ED8", "Jobs & Career Alerts", 84),
]


def list_active_newspapers(category: str | None = None) -> QuerySet[Newspaper]:
    queryset = Newspaper.objects.filter(is_active=True)
    if category:
        queryset = queryset.filter(category=category.strip().upper())
    return queryset


def create_newspaper(validated_data: dict) -> Newspaper:
    try:
        return Newspaper.objects.create(**validated_data)
    except IntegrityError as exc:
        error_text = str(exc).lower()
        if "slug" in error_text:
            raise ValidationError({"slug": "A newspaper with this slug already exists."})
        if "url" in error_text:
            raise ValidationError({"url": "A newspaper with this URL already exists."})
        raise ValidationError({"non_field_errors": ["Could not create newspaper due to database constraints."]})


def seed_default_newspapers() -> dict:
    created = 0
    existing = 0
    for slug, name, bangla_name, url, category, accent, tagline, order in DEFAULT_NEWSPAPERS_SEED:
        _, was_created = Newspaper.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "bangla_name": bangla_name,
                "url": url,
                "category": category,
                "accent_color": accent,
                "tagline": tagline,
                "sort_order": order,
                "is_active": True,
            },
        )
        if was_created:
            created += 1
        else:
            existing += 1
    return {"created": created, "existing": existing}
