# Bulgarian Legal Research Domains Configuration
# This file defines the specific domains and sources for Bulgarian legal research

BULGARIAN_LEGAL_DOMAINS = {
    # Primary Legal Information Sources
    "lex_bg": {
        "domain": "lex.bg",
        "description": "LexBG - Comprehensive Bulgarian legal database",
        "search_patterns": [
            "site:lex.bg",
            "lex.bg",
            "ЛексБГ"
        ],
        "focus_areas": ["законодателство", "съдебна практика", "нормативни актове"]
    },
    
    "vks_bg": {
        "domain": "vks.bg", 
        "description": "Supreme Court of Cassation - Върховен касационен съд",
        "search_patterns": [
            "site:vks.bg",
            "vks.bg",
            "върховен касационен съд"
        ],
        "focus_areas": ["съдебни решения", "касационна практика", "тълкувателни решения"]
    },
    
    "vss_bg": {
        "domain": "vss.bg",
        "description": "Supreme Administrative Court - Върховен административен съд", 
        "search_patterns": [
            "site:vss.bg",
            "vss.bg",
            "върховен административен съд"
        ],
        "focus_areas": ["административен процес", "държавна администрация", "обжалване"]
    },
    
    "justice_bg": {
        "domain": "justice.bg",
        "description": "Ministry of Justice - Министерство на правосъдието",
        "search_patterns": [
            "site:justice.bg",
            "justice.bg",
            "министерство на правосъдието"
        ],
        "focus_areas": ["законопроекти", "правни реформи", "нормативни актове"]
    },
    
    "parliament_bg": {
        "domain": "parliament.bg",
        "description": "National Assembly - Народно събрание",
        "search_patterns": [
            "site:parliament.bg",
            "parliament.bg",
            "народно събрание"
        ],
        "focus_areas": ["закони", "законопроекти", "парламентарни дебати"]
    },
    
    "cpc_bg": {
        "domain": "cpc.bg",
        "description": "Commission for Personal Data Protection - КЗЛД",
        "search_patterns": [
            "site:cpc.bg",
            "cpc.bg",
            "КЗЛД",
            "комисия защита лични данни"
        ],
        "focus_areas": ["защита на данните", "GDPR", "лични данни", "санкции"]
    },
    
    "dv_bg": {
        "domain": "dv.bg", 
        "description": "State Gazette - Държавен вестник",
        "search_patterns": [
            "site:dv.bg",
            "dv.bg",
            "държавен вестник"
        ],
        "focus_areas": ["официални публикации", "нови закони", "наредби", "решения"]
    },
    "vks_dominos": {
        "domain": "dominos.vks.bg", 
        "description": "VKS Case Database - ВКС Дела и решения",
        "search_patterns": [
            "site:dominos.vks.bg",
            "dominos.vks.bg",
            "ВКС дела"
        ],
        "focus_areas": ["съдебни решения", "касационна практика", "тълкувателни решения"]
    },
    "vss_dominos": {
        "domain": "dominos.vss.bg",
        "description": "VAS Case Database - ВАС Дела и решения", 
        "search_patterns": [
            "site:dominos.vss.bg",
            "dominos.vss.bg",
            "ВАС дела"
        ],
        "focus_areas": ["административни решения", "обжалване", "административен процес"]
    }
}

# Legal Practice Areas in Bulgarian
BULGARIAN_LEGAL_AREAS = {
    "corporate_law": {
        "bg_name": "корпоративно право",
        "keywords": ["търговски дружества", "капитал", "акции", "дялове", "управление", "съвет на директорите"],
        "related_domains": ["lex_bg", "justice_bg", "dv_bg"]
    },
    
    "administrative_law": {
        "bg_name": "административно право",
        "keywords": ["административен процес", "държавна администрация", "обжалване"],
        "related_domains": ["vss_bg", "justice_bg", "dv_bg"]
    },
    
    "civil_law": {
        "bg_name": "гражданско право",
        "keywords": ["договори", "обещения", "собственост", "задължения", "деликти"],
        "related_domains": ["vks_bg", "lex_bg", "justice_bg"]
    },
    
    "criminal_law": {
        "bg_name": "наказателно право",
        "keywords": ["престъпления", "наказания", "наказателен процес", "разследване"],
        "related_domains": ["vks_bg", "justice_bg", "lex_bg"]
    },
    
    "labor_law": {
        "bg_name": "трудово право",
        "keywords": ["трудови договори", "работно време", "заплащане", "увольнение", "трудови спорове"],
        "related_domains": ["lex_bg", "justice_bg", "vks_bg"]
    },
    
    "data_protection": {
        "bg_name": "защита на данните",
        "keywords": ["GDPR", "лични данни", "обработка", "съгласие", "нарушения", "санкции"],
        "related_domains": ["cpc_bg", "lex_bg", "dv_bg"]
    },
    
    "tax_law": {
        "bg_name": "данъчно право", 
        "keywords": ["данъци", "ДДС", "подоходен данък", "данъчни проверки", "обжалване"],
        "related_domains": ["lex_bg", "vss_bg", "dv_bg"]
    }
}

# Search Enhancement Patterns
BULGARIAN_SEARCH_ENHANCEMENTS = {
    "legal_terms": [
        "съдебна практика",
        "тълкувателно решение", 
        "нормативен акт",
        "правна норма",
        "съдебно решение",
        "касационно определение",
        "обжалване",
        "производство",
        "правна сила"
    ],
    
    "temporal_indicators": [
        "2025", "2024", "актуален", "в сила", "изменен", "отменен", "нов", "последен"
    ],
    
    "authority_indicators": [
        "ВКС", "ВАС", "съд", "прокуратура", "МП", "НС", "КЗЛД"
    ]
}

def get_domain_specific_search_pattern(domain_key: str, query: str) -> str:
    """Generate domain-specific search pattern for Bulgarian legal research"""
    if domain_key not in BULGARIAN_LEGAL_DOMAINS:
        return query
        
    domain_info = BULGARIAN_LEGAL_DOMAINS[domain_key]
    search_pattern = domain_info["search_patterns"][0]  # Primary pattern
    
    # Add Bulgarian legal terms enhancement
    enhanced_query = f"{query} {search_pattern}"
    
    # Add focus area keywords if relevant
    for focus_area in domain_info["focus_areas"]:
        if any(term in query.lower() for term in focus_area.split()):
            enhanced_query += f" {focus_area}"
            break
    
    return enhanced_query

def get_domains_for_legal_area(legal_area: str) -> list:
    """Get relevant domains for a specific legal area"""
    if legal_area in BULGARIAN_LEGAL_AREAS:
        return BULGARIAN_LEGAL_AREAS[legal_area]["related_domains"]
    return list(BULGARIAN_LEGAL_DOMAINS.keys())

def enhance_query_with_bulgarian_legal_terms(query: str) -> str:
    """Enhance query with Bulgarian legal terminology"""
    enhanced = query
    
    # Add temporal context
    enhanced += " 2025 OR 2024 OR актуален OR в сила"
    
    # Add authority context
    enhanced += " (съд OR решение OR практика OR закон)"
    
    return enhanced 