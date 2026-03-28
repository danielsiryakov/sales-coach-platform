"""
Seed the database with initial domain content.
Run with: python -m scripts.seed_data
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.core.database import async_session_maker, init_db
from app.models.database import (
    ScenarioTemplate, BusinessContext, PersonaTrait,
    Objection, CallType, DifficultyLevel
)


SCENARIO_TEMPLATES = [
    {
        "name": "Cold Call - Job Site Visit Follow-up",
        "description": "Following up after visiting a job site and leaving a card",
        "call_type": CallType.COLD_CALL,
        "base_prompt": "An insurance agent is calling you after they visited one of your job sites last week and left a business card. You weren't there but your foreman mentioned it. You're mildly curious but very busy.",
        "objectives": ["Build rapport", "Learn about current coverage situation", "Schedule a follow-up meeting"],
        "difficulty_level": DifficultyLevel.BEGINNER,
        "estimated_duration_minutes": 8,
    },
    {
        "name": "Cold Call - Phone Prospecting",
        "description": "Cold call from a purchased contractor list",
        "call_type": CallType.COLD_CALL,
        "base_prompt": "An insurance agent is cold calling you from a contractor directory. You get these calls often and usually brush them off quickly. You're skeptical but might listen if they say something interesting.",
        "objectives": ["Get past initial resistance", "Identify a pain point", "Create interest in a meeting"],
        "difficulty_level": DifficultyLevel.INTERMEDIATE,
        "estimated_duration_minutes": 10,
    },
    {
        "name": "Cold Call - Networking Event Follow-up",
        "description": "Following up after meeting at a trade association event",
        "call_type": CallType.COLD_CALL,
        "base_prompt": "An insurance agent is calling to follow up from a conversation at the local contractors association meeting last week. You remember chatting briefly but don't recall specifics.",
        "objectives": ["Remind prospect of meeting", "Deepen relationship", "Schedule review meeting"],
        "difficulty_level": DifficultyLevel.BEGINNER,
        "estimated_duration_minutes": 7,
    },
    {
        "name": "Warm Lead - Web Inquiry",
        "description": "Prospect submitted a quote request online",
        "call_type": CallType.WARM_LEAD,
        "base_prompt": "You filled out a quote request form online last night. You're actively shopping for insurance because your current policy is up for renewal in 6 weeks. You want competitive pricing but also good coverage.",
        "objectives": ["Understand current coverage", "Gather quote information", "Differentiate from competitors"],
        "difficulty_level": DifficultyLevel.INTERMEDIATE,
        "estimated_duration_minutes": 15,
    },
    {
        "name": "Warm Lead - Referral Introduction",
        "description": "Referred by an existing client",
        "call_type": CallType.WARM_LEAD,
        "base_prompt": "Your friend Dave (who runs a similar business) referred this insurance agent to you. Dave mentioned they helped him save money and handled a claim really well. You trust Dave's judgment but want to hear for yourself.",
        "objectives": ["Leverage referral trust", "Learn about prospect's business", "Schedule detailed review"],
        "difficulty_level": DifficultyLevel.BEGINNER,
        "estimated_duration_minutes": 12,
    },
    {
        "name": "Warm Lead - GC Certificate Requirement",
        "description": "Subcontractor needs coverage to work for a GC",
        "call_type": CallType.WARM_LEAD,
        "base_prompt": "A general contractor just offered you a big project but requires specific insurance limits you don't currently have. You need to figure out coverage quickly - the project starts in 3 weeks.",
        "objectives": ["Understand certificate requirements", "Quote appropriate coverage", "Expedite binding process"],
        "difficulty_level": DifficultyLevel.ADVANCED,
        "estimated_duration_minutes": 15,
    },
    {
        "name": "Renewal - Competitive Defense",
        "description": "Client received a lower quote from competitor",
        "call_type": CallType.RENEWAL,
        "base_prompt": "Your policy is up for renewal and another agent sent you a quote that's 15% cheaper. You like your current agent but money is tight. You want to see if they can match or beat the price.",
        "objectives": ["Understand competitor quote", "Identify coverage differences", "Demonstrate value", "Retain business"],
        "difficulty_level": DifficultyLevel.ADVANCED,
        "estimated_duration_minutes": 15,
    },
    {
        "name": "Renewal - Premium Increase Discussion",
        "description": "Presenting a renewal with a rate increase",
        "call_type": CallType.RENEWAL,
        "base_prompt": "Your agent is calling about your renewal. You've heard premiums are going up and you're frustrated - you haven't had any claims. You want to understand why and see what can be done about it.",
        "objectives": ["Explain rate increase factors", "Present coverage options", "Retain business", "Maintain relationship"],
        "difficulty_level": DifficultyLevel.EXPERT,
        "estimated_duration_minutes": 20,
    },
    {
        "name": "Cross-Sell - Workers Comp Addition",
        "description": "Current client needs to add workers comp",
        "call_type": CallType.CROSS_SELL,
        "base_prompt": "You've been a sole proprietor with just general liability, but you just hired your first employee. You know you need workers comp but you're worried about the cost.",
        "objectives": ["Explain WC requirements", "Quote coverage", "Address cost concerns", "Bind coverage"],
        "difficulty_level": DifficultyLevel.INTERMEDIATE,
        "estimated_duration_minutes": 12,
    },
    {
        "name": "Cross-Sell - Builder's Risk for New Project",
        "description": "Contractor needs builder's risk for a large project",
        "call_type": CallType.CROSS_SELL,
        "base_prompt": "You just signed a contract for a $2 million commercial renovation project. The contract requires you to carry builder's risk insurance. You've never purchased this before.",
        "objectives": ["Explain builder's risk coverage", "Gather project details", "Quote appropriate coverage", "Bind before project start"],
        "difficulty_level": DifficultyLevel.ADVANCED,
        "estimated_duration_minutes": 15,
    },
    {
        "name": "Claims - First Notice of Loss",
        "description": "Client calling to report a claim",
        "call_type": CallType.CLAIMS,
        "base_prompt": "One of your employees was injured on a job site this morning - fell off a ladder. He's at the hospital now. You need to report the claim and you're stressed about what happens next.",
        "objectives": ["Gather claim details", "Explain claims process", "Provide reassurance", "Document properly"],
        "difficulty_level": DifficultyLevel.INTERMEDIATE,
        "estimated_duration_minutes": 10,
    },
    {
        "name": "Claims - Follow-up on Frustrating Claim",
        "description": "Client unhappy with claim progress",
        "call_type": CallType.CLAIMS,
        "base_prompt": "You filed a claim 3 weeks ago and feel like nothing is happening. The adjuster hasn't returned your calls. You're angry and considering switching agents after this is resolved.",
        "objectives": ["De-escalate frustration", "Investigate claim status", "Advocate for client", "Repair relationship"],
        "difficulty_level": DifficultyLevel.EXPERT,
        "estimated_duration_minutes": 15,
    },
    {
        "name": "Review - Annual Policy Review",
        "description": "Scheduled annual coverage review",
        "call_type": CallType.REVIEW,
        "base_prompt": "Your insurance agent scheduled this annual review. Your business has grown - you added 2 employees and bought a new work truck. You want to make sure you're properly covered.",
        "objectives": ["Review current coverage", "Identify gaps", "Update policy as needed", "Strengthen relationship"],
        "difficulty_level": DifficultyLevel.INTERMEDIATE,
        "estimated_duration_minutes": 20,
    },
    {
        "name": "Review - New Account Onboarding",
        "description": "First meeting after binding new policy",
        "call_type": CallType.REVIEW,
        "base_prompt": "You just switched to this new insurance agency. This is your first meeting after the policy started. You want to understand your coverage better and know how things work.",
        "objectives": ["Explain coverage details", "Set service expectations", "Gather additional info", "Build relationship foundation"],
        "difficulty_level": DifficultyLevel.BEGINNER,
        "estimated_duration_minutes": 15,
    },
]

BUSINESS_CONTEXTS = [
    {
        "trade_name": "Residential General Contractor",
        "trade_code": "gc_residential",
        "description": "Small residential remodeling and construction company",
        "typical_operations": ["Kitchen/bath remodels", "Room additions", "Deck construction", "Basement finishing", "Whole house renovations"],
        "common_risks": ["Property damage during construction", "Worker injuries", "Subcontractor issues", "Customer property damage", "Tool theft"],
        "required_coverages": ["General Liability", "Workers Compensation", "Commercial Auto", "Inland Marine"],
        "revenue_range": {"min": 200000, "max": 2000000},
        "employee_range": {"min": 2, "max": 15},
        "subcontractor_usage": True,
        "equipment_intensive": True,
    },
    {
        "trade_name": "Commercial General Contractor",
        "trade_code": "gc_commercial",
        "description": "Commercial construction and tenant improvement company",
        "typical_operations": ["Office buildouts", "Retail construction", "Tenant improvements", "Commercial renovations", "Light industrial"],
        "common_risks": ["Delays and penalties", "Professional liability", "Large property exposures", "Multiple subcontractors", "Completion bonds"],
        "required_coverages": ["General Liability", "Workers Compensation", "Commercial Auto", "Umbrella", "Builder's Risk", "Professional Liability"],
        "revenue_range": {"min": 1000000, "max": 20000000},
        "employee_range": {"min": 5, "max": 50},
        "subcontractor_usage": True,
        "equipment_intensive": True,
    },
    {
        "trade_name": "Electrical Contractor",
        "trade_code": "electrical",
        "description": "Licensed electrical contractor for residential and commercial work",
        "typical_operations": ["New construction wiring", "Panel upgrades", "Commercial electrical", "EV charger installation", "Troubleshooting"],
        "common_risks": ["Electrical fires", "Shock injuries", "Code violations", "Property damage", "Professional errors"],
        "required_coverages": ["General Liability", "Workers Compensation", "Commercial Auto", "Professional Liability"],
        "revenue_range": {"min": 150000, "max": 3000000},
        "employee_range": {"min": 1, "max": 20},
        "subcontractor_usage": False,
        "equipment_intensive": False,
    },
    {
        "trade_name": "Roofing Contractor",
        "trade_code": "roofing",
        "description": "Residential and commercial roofing installation and repair",
        "typical_operations": ["Shingle installation", "Flat roof systems", "Roof repairs", "Storm damage restoration", "Gutter installation"],
        "common_risks": ["Falls from height", "Property damage during work", "Storm chasers/competition", "Material defects", "Wind damage to work"],
        "required_coverages": ["General Liability", "Workers Compensation", "Commercial Auto", "Inland Marine"],
        "revenue_range": {"min": 300000, "max": 5000000},
        "employee_range": {"min": 3, "max": 25},
        "subcontractor_usage": True,
        "equipment_intensive": True,
    },
    {
        "trade_name": "Plumbing Contractor",
        "trade_code": "plumbing",
        "description": "Licensed plumber for service, repair, and new construction",
        "typical_operations": ["Service calls", "Water heater installation", "Drain cleaning", "New construction rough-in", "Remodel plumbing"],
        "common_risks": ["Water damage from leaks", "Sewer backups", "Property damage", "Professional errors", "Mold resulting from work"],
        "required_coverages": ["General Liability", "Workers Compensation", "Commercial Auto", "Professional Liability"],
        "revenue_range": {"min": 200000, "max": 2500000},
        "employee_range": {"min": 1, "max": 15},
        "subcontractor_usage": False,
        "equipment_intensive": False,
    },
    {
        "trade_name": "HVAC Contractor",
        "trade_code": "hvac",
        "description": "Heating, ventilation, and air conditioning service and installation",
        "typical_operations": ["System installation", "Maintenance contracts", "Repair service", "Commercial HVAC", "Indoor air quality"],
        "common_risks": ["Refrigerant handling", "Electrical work", "Property damage", "Professional errors", "Fire hazards"],
        "required_coverages": ["General Liability", "Workers Compensation", "Commercial Auto", "Professional Liability", "Pollution Liability"],
        "revenue_range": {"min": 300000, "max": 4000000},
        "employee_range": {"min": 2, "max": 25},
        "subcontractor_usage": False,
        "equipment_intensive": True,
    },
    {
        "trade_name": "Excavation Contractor",
        "trade_code": "excavation",
        "description": "Site work, excavation, and utility installation",
        "typical_operations": ["Site grading", "Foundation excavation", "Utility trenching", "Septic installation", "Demolition"],
        "common_risks": ["Underground utility strikes", "Cave-ins", "Equipment accidents", "Property damage", "Environmental damage"],
        "required_coverages": ["General Liability", "Workers Compensation", "Commercial Auto", "Inland Marine", "Pollution Liability"],
        "revenue_range": {"min": 400000, "max": 5000000},
        "employee_range": {"min": 3, "max": 20},
        "subcontractor_usage": False,
        "equipment_intensive": True,
    },
    {
        "trade_name": "Painting Contractor",
        "trade_code": "painting",
        "description": "Interior and exterior painting for residential and commercial",
        "typical_operations": ["Interior painting", "Exterior painting", "Commercial painting", "Drywall repair", "Wallpaper installation"],
        "common_risks": ["Falls from ladders", "Property damage", "Lead paint exposure", "VOC exposure", "Overspray damage"],
        "required_coverages": ["General Liability", "Workers Compensation", "Commercial Auto"],
        "revenue_range": {"min": 100000, "max": 1500000},
        "employee_range": {"min": 1, "max": 15},
        "subcontractor_usage": True,
        "equipment_intensive": False,
    },
    {
        "trade_name": "Concrete/Masonry Contractor",
        "trade_code": "concrete",
        "description": "Concrete work and masonry construction",
        "typical_operations": ["Foundation work", "Flatwork", "Decorative concrete", "Brick/block work", "Retaining walls"],
        "common_risks": ["Structural failures", "Worker injuries", "Property damage", "Weather delays", "Material defects"],
        "required_coverages": ["General Liability", "Workers Compensation", "Commercial Auto", "Inland Marine"],
        "revenue_range": {"min": 250000, "max": 3000000},
        "employee_range": {"min": 3, "max": 20},
        "subcontractor_usage": False,
        "equipment_intensive": True,
    },
    {
        "trade_name": "Landscaping Contractor",
        "trade_code": "landscaping",
        "description": "Landscaping design, installation, and maintenance",
        "typical_operations": ["Lawn maintenance", "Landscape installation", "Irrigation", "Hardscaping", "Tree service"],
        "common_risks": ["Property damage", "Equipment injuries", "Pesticide exposure", "Tree falling damage", "Vehicle accidents"],
        "required_coverages": ["General Liability", "Workers Compensation", "Commercial Auto", "Inland Marine"],
        "revenue_range": {"min": 100000, "max": 2000000},
        "employee_range": {"min": 2, "max": 30},
        "subcontractor_usage": True,
        "equipment_intensive": True,
    },
]

PERSONA_TRAITS = [
    # Personality traits
    {"category": "personality", "name": "Skeptical", "description": "Distrustful of salespeople, needs proof for every claim", "behavioral_cues": ["Questions claims", "Asks for references", "Challenges statements"], "difficulty_modifier": 1.3},
    {"category": "personality", "name": "Friendly", "description": "Warm and conversational, enjoys chatting", "behavioral_cues": ["Makes small talk", "Shares personal details", "Laughs easily"], "difficulty_modifier": 0.8},
    {"category": "personality", "name": "Direct", "description": "No-nonsense, wants to get to the point quickly", "behavioral_cues": ["Short answers", "Interrupts tangents", "Asks 'bottom line'"], "difficulty_modifier": 1.0},
    {"category": "personality", "name": "Analytical", "description": "Detail-oriented, wants to understand everything", "behavioral_cues": ["Asks many questions", "Takes notes", "Requests documentation"], "difficulty_modifier": 1.2},

    # Buying behaviors
    {"category": "buying_behavior", "name": "Price-focused", "description": "Primary concern is getting the lowest price", "behavioral_cues": ["Asks about price immediately", "Compares to competitors", "Negotiates everything"], "difficulty_modifier": 1.3},
    {"category": "buying_behavior", "name": "Value-oriented", "description": "Wants to understand the value, not just price", "behavioral_cues": ["Asks about coverage details", "Interested in claims service", "Weighs options carefully"], "difficulty_modifier": 1.0},
    {"category": "buying_behavior", "name": "Relationship-driven", "description": "Values trust and personal connection", "behavioral_cues": ["Asks about agent experience", "Values responsiveness", "Loyal to good service"], "difficulty_modifier": 0.9},
    {"category": "buying_behavior", "name": "Impulsive", "description": "Makes quick decisions, doesn't overthink", "behavioral_cues": ["Ready to commit quickly", "Doesn't ask many questions", "Trusts gut feeling"], "difficulty_modifier": 0.7},

    # Emotional states
    {"category": "emotional_state", "name": "Busy/Rushed", "description": "Has limited time, easily distracted", "behavioral_cues": ["Short responses", "Mentions being busy", "May end call early"], "difficulty_modifier": 1.2},
    {"category": "emotional_state", "name": "Frustrated", "description": "Had a bad experience, currently annoyed", "behavioral_cues": ["Vents about problems", "Negative tone", "Needs validation"], "difficulty_modifier": 1.4},
    {"category": "emotional_state", "name": "Anxious", "description": "Worried about making wrong decision", "behavioral_cues": ["Asks 'what if' questions", "Seeks reassurance", "Hesitant to commit"], "difficulty_modifier": 1.1},
    {"category": "emotional_state", "name": "Confident", "description": "Knows what they want, assertive", "behavioral_cues": ["States requirements clearly", "Challenges expertise", "Negotiates firmly"], "difficulty_modifier": 1.2},
]

OBJECTIONS = [
    # Price objections
    {"category": "price", "objection_text": "That's way more than I'm paying now.", "difficulty_level": DifficultyLevel.INTERMEDIATE},
    {"category": "price", "objection_text": "I got a quote for half that price from another agent.", "difficulty_level": DifficultyLevel.ADVANCED},
    {"category": "price", "objection_text": "I can't afford that kind of increase right now.", "difficulty_level": DifficultyLevel.INTERMEDIATE},
    {"category": "price", "objection_text": "My buddy pays way less and he does the same work.", "difficulty_level": DifficultyLevel.ADVANCED},
    {"category": "price", "objection_text": "Why is insurance so expensive for contractors?", "difficulty_level": DifficultyLevel.BEGINNER},

    # Broker loyalty
    {"category": "loyalty", "objection_text": "I've been with my agent for 15 years, why would I switch?", "difficulty_level": DifficultyLevel.ADVANCED},
    {"category": "loyalty", "objection_text": "My current agent is a family friend.", "difficulty_level": DifficultyLevel.EXPERT},
    {"category": "loyalty", "objection_text": "I just renewed last month, I'm not looking.", "difficulty_level": DifficultyLevel.INTERMEDIATE},
    {"category": "loyalty", "objection_text": "My agent always takes care of me, I don't need another quote.", "difficulty_level": DifficultyLevel.ADVANCED},

    # Complacency
    {"category": "complacency", "objection_text": "I've never had a claim, why do I need better coverage?", "difficulty_level": DifficultyLevel.INTERMEDIATE},
    {"category": "complacency", "objection_text": "I'm fine with what I have, it's worked for years.", "difficulty_level": DifficultyLevel.INTERMEDIATE},
    {"category": "complacency", "objection_text": "Insurance is just a necessary evil, I don't think about it much.", "difficulty_level": DifficultyLevel.BEGINNER},
    {"category": "complacency", "objection_text": "My workers are careful, we don't really need workers comp.", "difficulty_level": DifficultyLevel.ADVANCED},

    # Process/timing concerns
    {"category": "process", "objection_text": "I don't have time to deal with this right now.", "difficulty_level": DifficultyLevel.INTERMEDIATE},
    {"category": "process", "objection_text": "I need to talk to my wife/partner first.", "difficulty_level": DifficultyLevel.BEGINNER},
    {"category": "process", "objection_text": "Can you just email me the info? I'll look at it later.", "difficulty_level": DifficultyLevel.INTERMEDIATE},
    {"category": "process", "objection_text": "Switching sounds like a hassle. Will there be a coverage gap?", "difficulty_level": DifficultyLevel.INTERMEDIATE},

    # Technical confusion
    {"category": "confusion", "objection_text": "I don't understand why I need both GL and Workers Comp.", "difficulty_level": DifficultyLevel.BEGINNER},
    {"category": "confusion", "objection_text": "What's the difference between all these coverage types?", "difficulty_level": DifficultyLevel.BEGINNER},
    {"category": "confusion", "objection_text": "Why do I need an umbrella? I already have liability.", "difficulty_level": DifficultyLevel.INTERMEDIATE},
    {"category": "confusion", "objection_text": "The GC is requiring limits I've never heard of.", "difficulty_level": DifficultyLevel.INTERMEDIATE},
]


async def seed_database():
    """Seed the database with initial data."""
    await init_db()

    async with async_session_maker() as db:
        # Check if already seeded
        from sqlalchemy import select
        result = await db.execute(select(ScenarioTemplate).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded, skipping...")
            return

        print("Seeding scenario templates...")
        for template_data in SCENARIO_TEMPLATES:
            template = ScenarioTemplate(**template_data)
            db.add(template)

        print("Seeding business contexts...")
        for context_data in BUSINESS_CONTEXTS:
            context = BusinessContext(**context_data)
            db.add(context)

        print("Seeding persona traits...")
        for trait_data in PERSONA_TRAITS:
            trait = PersonaTrait(**trait_data)
            db.add(trait)

        print("Seeding objections...")
        for objection_data in OBJECTIONS:
            objection = Objection(**objection_data)
            db.add(objection)

        await db.commit()
        print("Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
