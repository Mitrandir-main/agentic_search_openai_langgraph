# Bulgarian Legal Research Domains Configuration
# Simplified configuration focused on 4 core domains with court decisions

BULGARIAN_LEGAL_DOMAINS = {
    "ciela_net": {
        "domain": "ciela.net",
        "description": "Ciela - Bulgarian legal information and publishing (19,300+ indexed pages)"
    },
    "apis_bg": {
        "domain": "apis.bg",
        "description": "Апис - Bulgarian legal information and publishing (4,190+ indexed pages)"
    },
    "lakorda_com": {
        "domain": "lakorda.com",
        "description": "Лакорда - Legal news and information portal (11+ indexed pages)"
    }
}

def get_domain_list():
    """Get list of domain URLs for search"""
    return [domain_info["domain"] for domain_info in BULGARIAN_LEGAL_DOMAINS.values()]

def get_domain_descriptions():
    """Get domain descriptions for UI display"""
    return {key: info["description"] for key, info in BULGARIAN_LEGAL_DOMAINS.items()} 