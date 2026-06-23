DISEASES = {
    "malaria": {
        "name": "Malaria",
        "summary": "Life-threatening disease caused by Plasmodium parasites transmitted by infected Anopheles mosquitoes.",
        "symptoms": "Fever, chills, sweats, headache, body aches, nausea, and fatigue.",
        "vectors": "Primarily Anopheles mosquitoes.",
        "regions": "Sub-Saharan Africa, South Asia, Southeast Asia, and parts of Latin America.",
        "prevention": "Bed nets, repellent, antimalarial prophylaxis, and vector control.",
        "url": "https://www.who.int/news-room/fact-sheets/detail/malaria",
        "source": "WHO",
    },
    "dengue": {
        "name": "Dengue",
        "summary": "Viral infection causing flu-like illness that can develop into severe dengue.",
        "symptoms": "High fever, severe headache, joint and muscle pain, rash.",
        "vectors": "Aedes aegypti and Aedes albopictus.",
        "regions": "Tropical and subtropical regions worldwide.",
        "prevention": "Eliminate standing water and use repellent and screens.",
        "url": "https://www.cdc.gov/dengue/about/index.html",
        "source": "CDC",
    },
    "zika": {
        "name": "Zika",
        "summary": "Usually mild but linked to birth defects when contracted during pregnancy.",
        "symptoms": "Often asymptomatic; fever, rash, joint pain, and headache when present.",
        "vectors": "Aedes aegypti and Aedes albopictus.",
        "regions": "Tropical and subtropical areas worldwide.",
        "prevention": "Avoid mosquito bites, especially during pregnancy.",
        "url": "https://www.cdc.gov/zika/about/index.html",
        "source": "CDC",
    },
    "west_nile": {
        "name": "West Nile",
        "summary": "Leading cause of mosquito-borne disease in the continental United States.",
        "symptoms": "Most have no symptoms; fever, headache, body aches in some cases.",
        "vectors": "Culex species.",
        "regions": "North America, Europe, Africa, the Middle East, and West Asia.",
        "prevention": "Repellent and local mosquito abatement.",
        "url": "https://www.cdc.gov/west-nile-virus/about/index.html",
        "source": "CDC",
    },
    "chikungunya": {
        "name": "Chikungunya",
        "summary": "Viral infection causing fever and severe joint pain.",
        "symptoms": "Sudden high fever, severe joint pain, muscle pain, headache, and rash.",
        "vectors": "Aedes aegypti and Aedes albopictus.",
        "regions": "Africa, Asia, Europe, and the Americas.",
        "prevention": "Reduce container breeding sites and avoid daytime bites.",
        "url": "https://www.cdc.gov/chikungunya/about/index.html",
        "source": "CDC",
    },
    "yellow_fever": {
        "name": "Yellow fever",
        "summary": "Acute viral hemorrhagic disease; vaccination is highly effective.",
        "symptoms": "Fever, headache, jaundice, muscle pain, nausea, and fatigue.",
        "vectors": "Aedes aegypti and jungle-cycle species.",
        "regions": "Tropical Africa and South America.",
        "prevention": "Yellow fever vaccine and bite prevention.",
        "url": "https://www.who.int/news-room/fact-sheets/detail/yellow-fever",
        "source": "WHO",
    },
    "eee": {
        "name": "Eastern Equine Encephalitis (EEE)",
        "summary": "Rare but serious viral disease that can cause brain inflammation.",
        "symptoms": "Fever, headache, irritability, drowsiness, vomiting; severe neuroinvasive disease is possible.",
        "vectors": "Culiseta melanura and bridge vectors including Aedes and Culex.",
        "regions": "Eastern and Gulf Coast U.S., Great Lakes region.",
        "prevention": "Avoid mosquito exposure in swampy areas and use repellent.",
        "url": "https://www.cdc.gov/eastern-equine-encephalitis/about/index.html",
        "source": "CDC",
    },
    "heartworm": {
        "name": "Heartworm",
        "summary": "Serious and potentially fatal condition in dogs, cats, and other mammals.",
        "symptoms": "Cough, fatigue, decreased appetite, and weight loss in dogs.",
        "vectors": "Multiple mosquito species including Aedes and Culex.",
        "regions": "Endemic in all 50 U.S. states and many temperate/tropical regions.",
        "prevention": "Year-round veterinary preventives for pets.",
        "url": "https://www.heartwormsociety.org/pet-owner-resources/heartworm-basics",
        "source": "American Heartworm Society",
    },
}


def get_disease(slug: str) -> dict | None:
    return DISEASES.get(slug)


def list_diseases() -> list[dict]:
    return [{"slug": k, **v} for k, v in DISEASES.items()]
