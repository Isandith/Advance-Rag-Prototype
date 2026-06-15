"""Seed the providers collection with 70 test providers, each with a
real Gemini embedding, for search/testing purposes.

Usage:
    venv/Scripts/python.exe scripts/seed_providers.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import connect, disconnect, get_db
from app.models.provider import ProviderCreate
from app.provider.service import register_provider


PROVIDERS: list[dict] = [
    # Medical
    {"name": "Dr. Amara Silva", "profession": "Cardiologist", "domain": "medical",
     "work_description": "Diagnoses and treats heart conditions including arrhythmia, hypertension, and coronary artery disease.",
     "keywords": ["cardiologist", "heart", "cardiac", "hypertension", "ecg"], "reliability_score": 4.8},
    {"name": "Dr. Nuwan Perera", "profession": "Dermatologist", "domain": "medical",
     "work_description": "Treats skin conditions such as acne, eczema, psoriasis, and performs skin cancer screenings.",
     "keywords": ["dermatologist", "skin", "acne", "eczema", "rash"], "reliability_score": 4.6},
    {"name": "Dr. Ishara Fernando", "profession": "Pediatrician", "domain": "medical",
     "work_description": "Provides medical care for infants, children, and adolescents including vaccinations and check-ups.",
     "keywords": ["pediatrician", "children", "vaccination", "infant", "checkup"], "reliability_score": 4.9},
    {"name": "Dr. Kasun Jayawardena", "profession": "Orthopedic Surgeon", "domain": "medical",
     "work_description": "Specializes in bone, joint, and muscle injuries including fractures, sports injuries, and arthritis.",
     "keywords": ["orthopedic", "bones", "joints", "fracture", "surgeon"], "reliability_score": 4.7},
    {"name": "Dr. Tharushi Bandara", "profession": "Dentist", "domain": "medical",
     "work_description": "General dentistry including cleanings, fillings, root canals, and cosmetic dental work.",
     "keywords": ["dentist", "teeth", "dental", "cavity", "root canal"], "reliability_score": 4.5},
    {"name": "Dr. Ruwan Gunasekara", "profession": "Psychiatrist", "domain": "medical",
     "work_description": "Diagnoses and treats mental health conditions such as anxiety, depression, and bipolar disorder.",
     "keywords": ["psychiatrist", "mental health", "anxiety", "depression", "therapy"], "reliability_score": 4.7},
    {"name": "Dr. Sanduni Wickramasinghe", "profession": "Ophthalmologist", "domain": "medical",
     "work_description": "Eye care specialist treating cataracts, glaucoma, and performing vision correction surgery.",
     "keywords": ["ophthalmologist", "eyes", "vision", "cataract", "glaucoma"], "reliability_score": 4.6},
    {"name": "Dr. Dilshan Rajapaksha", "profession": "General Practitioner", "domain": "medical",
     "work_description": "Provides general health checkups, diagnoses common illnesses, and refers to specialists.",
     "keywords": ["gp", "doctor", "general practitioner", "checkup", "clinic"], "reliability_score": 4.4},
    {"name": "Dr. Hashini Mendis", "profession": "Gynecologist", "domain": "medical",
     "work_description": "Women's health specialist providing prenatal care, fertility consultations, and gynecological exams.",
     "keywords": ["gynecologist", "women's health", "prenatal", "fertility", "obgyn"], "reliability_score": 4.8},
    {"name": "Dr. Chamara Liyanage", "profession": "Physiotherapist", "domain": "medical",
     "work_description": "Rehabilitates patients recovering from injury or surgery using physical therapy techniques.",
     "keywords": ["physiotherapist", "rehabilitation", "physical therapy", "injury", "recovery"], "reliability_score": 4.5},

    # Legal
    {"name": "Anjali Wijesinghe", "profession": "Corporate Lawyer", "domain": "legal",
     "work_description": "Advises businesses on mergers, acquisitions, contracts, and corporate governance.",
     "keywords": ["lawyer", "corporate law", "contracts", "mergers", "business law"], "reliability_score": 4.7},
    {"name": "Saman Karunaratne", "profession": "Family Lawyer", "domain": "legal",
     "work_description": "Handles divorce, child custody, adoption, and other family law matters.",
     "keywords": ["lawyer", "family law", "divorce", "custody", "adoption"], "reliability_score": 4.6},
    {"name": "Priyanka De Zoysa", "profession": "Criminal Defense Attorney", "domain": "legal",
     "work_description": "Represents clients facing criminal charges and provides courtroom defense.",
     "keywords": ["lawyer", "criminal defense", "attorney", "court", "legal defense"], "reliability_score": 4.5},
    {"name": "Tilak Senanayake", "profession": "Real Estate Lawyer", "domain": "legal",
     "work_description": "Handles property transactions, title disputes, and lease agreements.",
     "keywords": ["lawyer", "real estate", "property law", "title", "lease"], "reliability_score": 4.4},
    {"name": "Nadeesha Abeysekara", "profession": "Immigration Lawyer", "domain": "legal",
     "work_description": "Assists with visa applications, citizenship, and immigration appeals.",
     "keywords": ["lawyer", "immigration", "visa", "citizenship", "legal aid"], "reliability_score": 4.6},
    {"name": "Roshan Dissanayake", "profession": "Tax Attorney", "domain": "legal",
     "work_description": "Provides legal advice on tax disputes, planning, and compliance for individuals and businesses.",
     "keywords": ["lawyer", "tax law", "tax attorney", "compliance", "tax planning"], "reliability_score": 4.5},
    {"name": "Geetha Ranatunga", "profession": "Intellectual Property Lawyer", "domain": "legal",
     "work_description": "Handles trademark, copyright, and patent registration and disputes.",
     "keywords": ["lawyer", "intellectual property", "trademark", "patent", "copyright"], "reliability_score": 4.7},
    {"name": "Asela Gunawardena", "profession": "Employment Lawyer", "domain": "legal",
     "work_description": "Advises on workplace disputes, wrongful termination, and labor law compliance.",
     "keywords": ["lawyer", "employment law", "labor law", "workplace dispute", "termination"], "reliability_score": 4.4},

    # Tech
    {"name": "Yasiru Madushanka", "profession": "Web Developer", "domain": "tech",
     "work_description": "Builds responsive websites and web applications using React, Node.js, and modern frameworks.",
     "keywords": ["web developer", "react", "nodejs", "frontend", "javascript"], "reliability_score": 4.6},
    {"name": "Dilini Senarathne", "profession": "Mobile App Developer", "domain": "tech",
     "work_description": "Develops cross-platform mobile apps for iOS and Android using Flutter and React Native.",
     "keywords": ["app developer", "mobile app", "flutter", "ios", "android"], "reliability_score": 4.5},
    {"name": "Pasindu Wijeratne", "profession": "Cloud Architect", "domain": "tech",
     "work_description": "Designs and manages scalable cloud infrastructure on AWS, Azure, and GCP.",
     "keywords": ["cloud architect", "aws", "azure", "devops", "infrastructure"], "reliability_score": 4.8},
    {"name": "Madhavi Ekanayake", "profession": "Cybersecurity Consultant", "domain": "tech",
     "work_description": "Performs security audits, penetration testing, and helps secure IT systems.",
     "keywords": ["cybersecurity", "penetration testing", "security audit", "network security", "consultant"], "reliability_score": 4.7},
    {"name": "Lahiru Pathirana", "profession": "Data Scientist", "domain": "tech",
     "work_description": "Builds machine learning models and performs data analysis for business insights.",
     "keywords": ["data scientist", "machine learning", "data analysis", "python", "ai"], "reliability_score": 4.6},
    {"name": "Sachini Herath", "profession": "UI/UX Designer", "domain": "tech",
     "work_description": "Designs user interfaces and experiences for web and mobile products.",
     "keywords": ["ui designer", "ux designer", "product design", "figma", "wireframes"], "reliability_score": 4.5},
    {"name": "Chathura Rathnayake", "profession": "IT Support Technician", "domain": "tech",
     "work_description": "Provides desktop support, network troubleshooting, and hardware repair for businesses.",
     "keywords": ["it support", "tech support", "computer repair", "network troubleshooting", "helpdesk"], "reliability_score": 4.3},
    {"name": "Oshadhi Kodithuwakku", "profession": "Database Administrator", "domain": "tech",
     "work_description": "Manages and optimizes databases including MongoDB, PostgreSQL, and MySQL.",
     "keywords": ["database administrator", "mongodb", "sql", "postgresql", "dba"], "reliability_score": 4.6},

    # Finance
    {"name": "Kavindu Amarasinghe", "profession": "Accountant", "domain": "finance",
     "work_description": "Provides bookkeeping, tax filing, and financial statement preparation for small businesses.",
     "keywords": ["accountant", "bookkeeping", "tax filing", "financial statements", "cpa"], "reliability_score": 4.5},
    {"name": "Niluka Jayasuriya", "profession": "Financial Advisor", "domain": "finance",
     "work_description": "Helps clients plan investments, retirement savings, and wealth management strategies.",
     "keywords": ["financial advisor", "investment", "retirement planning", "wealth management", "portfolio"], "reliability_score": 4.7},
    {"name": "Buddhika Wickramaratne", "profession": "Mortgage Broker", "domain": "finance",
     "work_description": "Helps clients find and secure home loans from various lenders at competitive rates.",
     "keywords": ["mortgage broker", "home loan", "mortgage rates", "loan application", "refinancing"], "reliability_score": 4.4},
    {"name": "Anushka Premaratne", "profession": "Insurance Agent", "domain": "finance",
     "work_description": "Provides life, health, and property insurance policies tailored to client needs.",
     "keywords": ["insurance agent", "life insurance", "health insurance", "policy", "coverage"], "reliability_score": 4.3},
    {"name": "Janaka Senevirathne", "profession": "Auditor", "domain": "finance",
     "work_description": "Conducts financial audits to ensure regulatory compliance and accuracy for organizations.",
     "keywords": ["auditor", "financial audit", "compliance", "internal audit", "accounting"], "reliability_score": 4.6},
    {"name": "Thilini Gamage", "profession": "Tax Consultant", "domain": "finance",
     "work_description": "Assists individuals and businesses with tax preparation and minimizing tax liability.",
     "keywords": ["tax consultant", "tax preparation", "tax return", "tax advice", "vat"], "reliability_score": 4.5},

    # Home services
    {"name": "Ranil Gunatilake", "profession": "Plumber", "domain": "home services",
     "work_description": "Repairs leaks, installs pipes, and fixes plumbing fixtures for homes and offices.",
     "keywords": ["plumber", "plumbing", "leak repair", "pipe installation", "drain cleaning"], "reliability_score": 4.4},
    {"name": "Sunil Karunarathna", "profession": "Electrician", "domain": "home services",
     "work_description": "Installs and repairs electrical wiring, outlets, and lighting systems safely.",
     "keywords": ["electrician", "wiring", "electrical repair", "lighting", "circuit breaker"], "reliability_score": 4.5},
    {"name": "Mahinda Wijesundara", "profession": "Carpenter", "domain": "home services",
     "work_description": "Builds and repairs furniture, cabinets, doors, and custom woodwork.",
     "keywords": ["carpenter", "woodwork", "furniture", "cabinets", "joinery"], "reliability_score": 4.3},
    {"name": "Champika Rodrigo", "profession": "House Cleaner", "domain": "home services",
     "work_description": "Provides deep cleaning, regular housekeeping, and move-in/move-out cleaning services.",
     "keywords": ["house cleaner", "cleaning service", "housekeeping", "deep cleaning", "maid"], "reliability_score": 4.2},
    {"name": "Indika Samaraweera", "profession": "Painter", "domain": "home services",
     "work_description": "Provides interior and exterior painting services for residential and commercial properties.",
     "keywords": ["painter", "house painting", "interior painting", "exterior painting", "wall paint"], "reliability_score": 4.3},
    {"name": "Nimal Athukorala", "profession": "Gardener", "domain": "home services",
     "work_description": "Maintains gardens, lawns, and landscaping including pruning and planting.",
     "keywords": ["gardener", "landscaping", "lawn care", "pruning", "garden maintenance"], "reliability_score": 4.1},
    {"name": "Priyantha Ratnayake", "profession": "Pest Control Technician", "domain": "home services",
     "work_description": "Treats homes for termites, rodents, and other pest infestations.",
     "keywords": ["pest control", "termite treatment", "rodent control", "exterminator", "fumigation"], "reliability_score": 4.2},
    {"name": "Wasantha Kularatne", "profession": "AC Repair Technician", "domain": "home services",
     "work_description": "Services, repairs, and installs air conditioning units for homes and offices.",
     "keywords": ["ac repair", "air conditioning", "hvac", "ac installation", "ac servicing"], "reliability_score": 4.4},
    {"name": "Deepal Wanigasekara", "profession": "Locksmith", "domain": "home services",
     "work_description": "Provides lock installation, repair, and emergency lockout services.",
     "keywords": ["locksmith", "lock repair", "key cutting", "lockout service", "security locks"], "reliability_score": 4.3},

    # Automotive
    {"name": "Asanka Weerasinghe", "profession": "Auto Mechanic", "domain": "automotive",
     "work_description": "Diagnoses and repairs engine, brake, and transmission issues for cars and vans.",
     "keywords": ["auto mechanic", "car repair", "engine repair", "brakes", "transmission"], "reliability_score": 4.4},
    {"name": "Gihan Fonseka", "profession": "Auto Electrician", "domain": "automotive",
     "work_description": "Repairs vehicle electrical systems including batteries, alternators, and wiring.",
     "keywords": ["auto electrician", "car electrical", "battery", "alternator", "wiring repair"], "reliability_score": 4.3},
    {"name": "Ranjith Pemasiri", "profession": "Tyre Specialist", "domain": "automotive",
     "work_description": "Provides tyre replacement, wheel alignment, and balancing services.",
     "keywords": ["tyre specialist", "tire replacement", "wheel alignment", "tire balancing", "tyres"], "reliability_score": 4.2},
    {"name": "Damith Ariyaratne", "profession": "Car Detailer", "domain": "automotive",
     "work_description": "Offers professional car washing, waxing, and interior detailing services.",
     "keywords": ["car detailer", "car wash", "car detailing", "waxing", "interior cleaning"], "reliability_score": 4.1},

    # Education
    {"name": "Manori Jayatilaka", "profession": "Math Tutor", "domain": "education",
     "work_description": "Provides private tutoring in mathematics for school and university students.",
     "keywords": ["math tutor", "tutoring", "mathematics", "exam preparation", "private lessons"], "reliability_score": 4.6},
    {"name": "Sampath Wijewardena", "profession": "English Tutor", "domain": "education",
     "work_description": "Teaches English language skills including grammar, writing, and conversation practice.",
     "keywords": ["english tutor", "language tutor", "grammar", "writing skills", "esl"], "reliability_score": 4.5},
    {"name": "Kumudu Rajaguru", "profession": "Piano Teacher", "domain": "education",
     "work_description": "Offers piano lessons for beginners to advanced students of all ages.",
     "keywords": ["piano teacher", "music lessons", "piano lessons", "music tutor", "instrument lessons"], "reliability_score": 4.7},
    {"name": "Nayana Wickramage", "profession": "Career Counselor", "domain": "education",
     "work_description": "Guides students and professionals on career planning and university admissions.",
     "keywords": ["career counselor", "career guidance", "university admissions", "career planning", "counseling"], "reliability_score": 4.4},
    {"name": "Hemantha Suraweera", "profession": "Driving Instructor", "domain": "education",
     "work_description": "Teaches driving skills and prepares students for their driving license test.",
     "keywords": ["driving instructor", "driving lessons", "license test", "driving school", "road safety"], "reliability_score": 4.3},

    # Creative & marketing
    {"name": "Vindya Abeywickrama", "profession": "Graphic Designer", "domain": "creative",
     "work_description": "Creates logos, branding materials, and marketing graphics for businesses.",
     "keywords": ["graphic designer", "branding", "logo design", "marketing materials", "illustration"], "reliability_score": 4.5},
    {"name": "Janith Kumarasiri", "profession": "Photographer", "domain": "creative",
     "work_description": "Provides event, portrait, and product photography services.",
     "keywords": ["photographer", "event photography", "portrait photography", "product photography", "photo shoot"], "reliability_score": 4.6},
    {"name": "Imesha Goonetilleke", "profession": "Videographer", "domain": "creative",
     "work_description": "Produces promotional videos, event coverage, and short films.",
     "keywords": ["videographer", "video production", "event videography", "promotional video", "editing"], "reliability_score": 4.5},
    {"name": "Akila Senadheera", "profession": "Social Media Manager", "domain": "marketing",
     "work_description": "Manages social media accounts, content calendars, and ad campaigns for brands.",
     "keywords": ["social media manager", "content marketing", "social media ads", "brand strategy", "digital marketing"], "reliability_score": 4.4},
    {"name": "Sewwandi Hettiarachchi", "profession": "Copywriter", "domain": "marketing",
     "work_description": "Writes persuasive marketing copy for websites, ads, and email campaigns.",
     "keywords": ["copywriter", "marketing copy", "content writing", "ad copy", "email marketing"], "reliability_score": 4.3},
    {"name": "Tharindu Madurasinghe", "profession": "SEO Specialist", "domain": "marketing",
     "work_description": "Optimizes websites for search engines to improve organic traffic and rankings.",
     "keywords": ["seo specialist", "search engine optimization", "organic traffic", "keyword research", "seo audit"], "reliability_score": 4.5},

    # Events & hospitality
    {"name": "Disna Wijepala", "profession": "Event Planner", "domain": "events",
     "work_description": "Plans and coordinates weddings, corporate events, and private parties.",
     "keywords": ["event planner", "wedding planning", "corporate events", "party planning", "event coordination"], "reliability_score": 4.6},
    {"name": "Ajith Galappaththi", "profession": "Caterer", "domain": "events",
     "work_description": "Provides catering services for weddings, parties, and corporate functions.",
     "keywords": ["caterer", "catering service", "wedding catering", "food service", "menu planning"], "reliability_score": 4.4},
    {"name": "Shanika Dharmasena", "profession": "DJ", "domain": "events",
     "work_description": "Provides music and entertainment services for parties, weddings, and events.",
     "keywords": ["dj", "wedding dj", "party music", "event entertainment", "sound system"], "reliability_score": 4.3},
    {"name": "Lakshman Edirisinghe", "profession": "Hotel Concierge", "domain": "hospitality",
     "work_description": "Assists hotel guests with bookings, recommendations, and travel arrangements.",
     "keywords": ["concierge", "hotel services", "travel arrangements", "guest services", "bookings"], "reliability_score": 4.2},

    # Fitness & wellness
    {"name": "Heshan Wanninayake", "profession": "Personal Trainer", "domain": "fitness",
     "work_description": "Designs personalized workout plans and provides one-on-one fitness coaching.",
     "keywords": ["personal trainer", "fitness coach", "workout plan", "strength training", "gym"], "reliability_score": 4.6},
    {"name": "Pavithra Kodikara", "profession": "Yoga Instructor", "domain": "fitness",
     "work_description": "Teaches yoga classes for flexibility, relaxation, and overall wellness.",
     "keywords": ["yoga instructor", "yoga classes", "flexibility", "meditation", "wellness"], "reliability_score": 4.7},
    {"name": "Ranga Dassanayake", "profession": "Nutritionist", "domain": "fitness",
     "work_description": "Provides diet plans and nutritional guidance for weight management and health goals.",
     "keywords": ["nutritionist", "diet plan", "weight loss", "nutrition advice", "meal planning"], "reliability_score": 4.5},
    {"name": "Methsarani Liyanagama", "profession": "Massage Therapist", "domain": "fitness",
     "work_description": "Provides therapeutic massage for stress relief, muscle pain, and relaxation.",
     "keywords": ["massage therapist", "therapeutic massage", "stress relief", "muscle pain", "relaxation"], "reliability_score": 4.4},

    # Pets
    {"name": "Sashika Munasinghe", "profession": "Veterinarian", "domain": "pets",
     "work_description": "Provides medical care, vaccinations, and surgery for pets and farm animals.",
     "keywords": ["veterinarian", "vet", "pet health", "animal vaccination", "pet surgery"], "reliability_score": 4.7},
    {"name": "Nalin Wanigasinghe", "profession": "Dog Trainer", "domain": "pets",
     "work_description": "Trains dogs for obedience, behavior correction, and basic commands.",
     "keywords": ["dog trainer", "dog training", "obedience training", "puppy training", "pet behavior"], "reliability_score": 4.4},
    {"name": "Iresha Bulathwatte", "profession": "Pet Groomer", "domain": "pets",
     "work_description": "Provides grooming services including bathing, haircuts, and nail trimming for pets.",
     "keywords": ["pet groomer", "dog grooming", "cat grooming", "pet bathing", "nail trimming"], "reliability_score": 4.3},

    # Construction & real estate
    {"name": "Upul Rathnasiri", "profession": "Civil Engineer", "domain": "construction",
     "work_description": "Designs and oversees construction of buildings, roads, and infrastructure projects.",
     "keywords": ["civil engineer", "construction", "structural design", "building plans", "infrastructure"], "reliability_score": 4.6},
    {"name": "Chandika Wijesooriya", "profession": "Architect", "domain": "construction",
     "work_description": "Designs residential and commercial building plans and oversees construction projects.",
     "keywords": ["architect", "building design", "architectural plans", "construction design", "blueprints"], "reliability_score": 4.7},
    {"name": "Rasika Hapuarachchi", "profession": "Real Estate Agent", "domain": "real estate",
     "work_description": "Helps clients buy, sell, and rent residential and commercial properties.",
     "keywords": ["real estate agent", "property sale", "property rental", "house hunting", "realtor"], "reliability_score": 4.5},
    {"name": "Bandula Kalansooriya", "profession": "Interior Designer", "domain": "construction",
     "work_description": "Designs interior spaces for homes and offices including furniture and decor selection.",
     "keywords": ["interior designer", "home decor", "interior design", "space planning", "furniture selection"], "reliability_score": 4.4},
    {"name": "Sanjeewa Madhushanka", "profession": "Surveyor", "domain": "construction",
     "work_description": "Conducts land surveys for construction, boundary disputes, and property development.",
     "keywords": ["surveyor", "land survey", "boundary survey", "property measurement", "topographic survey"], "reliability_score": 4.3},

    # Logistics & misc
    {"name": "Chamal Wijetunga", "profession": "Moving Services Provider", "domain": "logistics",
     "work_description": "Provides packing, moving, and relocation services for homes and offices.",
     "keywords": ["moving services", "relocation", "packing", "movers", "furniture moving"], "reliability_score": 4.2},
    {"name": "Dineshi Ratwatte", "profession": "Courier Service Provider", "domain": "logistics",
     "work_description": "Delivers parcels and documents locally and nationwide with tracking.",
     "keywords": ["courier service", "parcel delivery", "document delivery", "shipping", "tracking"], "reliability_score": 4.1},
    {"name": "Mevan Karunatilaka", "profession": "Translator", "domain": "language services",
     "work_description": "Provides translation and interpretation services for documents and meetings.",
     "keywords": ["translator", "interpretation", "document translation", "language services", "multilingual"], "reliability_score": 4.5},
    {"name": "Oshani Senaratne", "profession": "Notary Public", "domain": "legal",
     "work_description": "Certifies and witnesses signing of legal documents and affidavits.",
     "keywords": ["notary public", "document certification", "affidavit", "notarization", "legal documents"], "reliability_score": 4.4},

    # Same gigs, different providers (competing options at different rates/quality)
    {"name": "Dr. Malindu Wijeratne", "profession": "Cardiologist", "domain": "medical",
     "work_description": "Budget-friendly cardiology consultations for arrhythmia, hypertension, and routine heart checkups.",
     "keywords": ["cardiologist", "heart", "cardiac", "hypertension", "ecg"], "reliability_score": 3.9},
    {"name": "Dr. Ayesha Ranasinghe", "profession": "Cardiologist", "domain": "medical",
     "work_description": "Premium cardiology care with advanced diagnostics for coronary artery disease and heart failure.",
     "keywords": ["cardiologist", "heart specialist", "cardiac care", "coronary", "heart failure"], "reliability_score": 4.9},
    {"name": "Nilantha Jayakody", "profession": "Plumber", "domain": "home services",
     "work_description": "Affordable plumbing repairs for leaks, clogged drains, and basic pipe fitting.",
     "keywords": ["plumber", "plumbing", "leak repair", "drain cleaning", "pipe fitting"], "reliability_score": 3.7},
    {"name": "Roshantha Dewapriya", "profession": "Plumber", "domain": "home services",
     "work_description": "Premium plumbing services including bathroom renovations, water heater installation, and emergency callouts.",
     "keywords": ["plumber", "plumbing", "bathroom renovation", "water heater", "emergency plumber"], "reliability_score": 4.8},
    {"name": "Kalana Wijesiri", "profession": "Web Developer", "domain": "tech",
     "work_description": "Budget website development for small businesses using WordPress and simple templates.",
     "keywords": ["web developer", "wordpress", "website design", "small business website", "frontend"], "reliability_score": 3.8},
    {"name": "Hirushi Abeyrathne", "profession": "Web Developer", "domain": "tech",
     "work_description": "High-end custom web application development using React, Node.js, and cloud deployment.",
     "keywords": ["web developer", "react", "nodejs", "custom web app", "full stack"], "reliability_score": 4.9},
    {"name": "Sujeewa Bandaranayake", "profession": "Electrician", "domain": "home services",
     "work_description": "Quick and affordable electrical repairs for outlets, switches, and minor wiring issues.",
     "keywords": ["electrician", "wiring", "electrical repair", "outlets", "switches"], "reliability_score": 3.6},
    {"name": "Charith Wimalasena", "profession": "Electrician", "domain": "home services",
     "work_description": "Certified electrician for full home rewiring, panel upgrades, and commercial installations.",
     "keywords": ["electrician", "rewiring", "panel upgrade", "commercial electrical", "licensed electrician"], "reliability_score": 4.8},
    {"name": "Damitha Senanayake", "profession": "Corporate Lawyer", "domain": "legal",
     "work_description": "Affordable legal advice for startups on contracts, incorporation, and basic compliance.",
     "keywords": ["lawyer", "corporate law", "startup legal", "incorporation", "contracts"], "reliability_score": 3.9},
    {"name": "Kithmina Rajapakse", "profession": "Corporate Lawyer", "domain": "legal",
     "work_description": "Top-tier corporate legal counsel for large mergers, acquisitions, and international business deals.",
     "keywords": ["lawyer", "corporate law", "mergers and acquisitions", "international business", "legal counsel"], "reliability_score": 4.9},
    {"name": "Pubudu Ekanayake", "profession": "Personal Trainer", "domain": "fitness",
     "work_description": "Group fitness sessions and budget workout plans for general fitness goals.",
     "keywords": ["personal trainer", "group fitness", "workout plan", "fitness coach", "exercise"], "reliability_score": 3.8},
    {"name": "Yashoda Karunaratne", "profession": "Personal Trainer", "domain": "fitness",
     "work_description": "Elite one-on-one personal training with custom nutrition plans for athletes.",
     "keywords": ["personal trainer", "elite training", "athlete coaching", "nutrition plan", "strength training"], "reliability_score": 4.9},
    {"name": "Ranindu Gunaratne", "profession": "Photographer", "domain": "creative",
     "work_description": "Affordable photography for small events and basic portrait sessions.",
     "keywords": ["photographer", "event photography", "portrait photography", "budget photography", "photo session"], "reliability_score": 3.7},
    {"name": "Senuri Wickramaarachchi", "profession": "Photographer", "domain": "creative",
     "work_description": "Premium wedding and commercial photography with professional editing and prints.",
     "keywords": ["photographer", "wedding photography", "commercial photography", "professional editing", "photo prints"], "reliability_score": 4.9},
]


async def main() -> None:
    await connect()
    db = get_db()

    existing = await db["providers"].count_documents({})
    print(f"Existing providers in collection: {existing}")

    existing_names = {
        doc["name"] async for doc in db["providers"].find({}, {"name": 1})
    }

    to_insert = [entry for entry in PROVIDERS if entry["name"] not in existing_names]
    print(f"New providers to insert: {len(to_insert)} (skipping {len(PROVIDERS) - len(to_insert)} already present)")

    inserted = 0
    for entry in to_insert:
        provider = ProviderCreate(
            name=entry["name"],
            profession=entry["profession"],
            work_description=entry["work_description"],
            reliability_score=entry["reliability_score"],
            keywords=entry["keywords"],
            domain=entry["domain"],
        )
        result = await register_provider(provider)
        inserted += 1
        print(f"[{inserted}/{len(to_insert)}] Inserted {result.name} ({result.profession})")

    total = await db["providers"].count_documents({})
    print(f"Done. Total providers in collection: {total}")

    await disconnect()


if __name__ == "__main__":
    asyncio.run(main())
