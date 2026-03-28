import random
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import (
    ScenarioTemplate, BusinessContext, PersonaTrait,
    Objection, DifficultyLevel
)


# First names by voice gender
MALE_NAMES = ["Mike", "Dave", "Carlos", "Jim", "Tom", "Steve", "Bob", "Rick", "Joe", "Dan"]
FEMALE_NAMES = ["Jennifer", "Sarah", "Maria", "Lisa", "Amy", "Karen", "Sue", "Beth", "Kim", "Pam"]

# Company name templates
COMPANY_TEMPLATES = [
    "{last_name} {trade}",
    "{last_name} & Sons {trade}",
    "{last_name} {trade} LLC",
    "{city} {trade}",
    "{adjective} {trade}",
    "{last_name}'s {trade}",
]

LAST_NAMES = ["Johnson", "Thompson", "Martinez", "Williams", "Davis", "Garcia", "Wilson", "Anderson", "Taylor", "Brown"]
CITIES = ["Metro", "Valley", "Summit", "Pacific", "Mountain", "Coastal", "Central", "Northern", "Southern", "Eastern"]
ADJECTIVES = ["Quality", "Premier", "Pro", "Elite", "Expert", "Reliable", "Trusted", "Superior", "Master", "Precision"]


class PersonaGenerator:
    """Generates dynamic personas for practice calls."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(
        self,
        scenario_template: ScenarioTemplate,
        business_context: BusinessContext,
        difficulty_level: DifficultyLevel,
        voice_gender: str = "male",  # or "female"
    ) -> Dict[str, Any]:
        """Generate a complete persona for the practice call."""

        # Select traits based on difficulty
        traits = await self._select_traits(difficulty_level)

        # Select objections based on difficulty
        objections = await self._select_objections(difficulty_level)

        # Generate name and company
        first_name = self._generate_name(voice_gender)
        last_name = random.choice(LAST_NAMES)
        company_name = self._generate_company_name(last_name, business_context)

        # Generate business details
        business_details = self._generate_business_details(business_context, difficulty_level)

        # Build the system prompt
        system_prompt = self._build_system_prompt(
            scenario=scenario_template,
            context=business_context,
            name=first_name,
            company=company_name,
            business_details=business_details,
            traits=traits,
            objections=objections,
        )

        return {
            "name": f"{first_name} {last_name}",
            "first_name": first_name,
            "last_name": last_name,
            "company": company_name,
            "trade": business_context.trade_name,
            "business_details": business_details,
            "traits": [t.name for t in traits],
            "trait_ids": [t.id for t in traits],
            "objections": [o.objection_text for o in objections],
            "objection_ids": [o.id for o in objections],
            "system_prompt": system_prompt,
            "difficulty_level": difficulty_level.value,
        }

    async def _select_traits(self, difficulty: DifficultyLevel) -> List[PersonaTrait]:
        """Select personality traits based on difficulty."""
        result = await self.db.execute(select(PersonaTrait))
        all_traits = result.scalars().all()

        if not all_traits:
            return []

        # Group by category
        by_category: Dict[str, List[PersonaTrait]] = {}
        for t in all_traits:
            if t.category not in by_category:
                by_category[t.category] = []
            by_category[t.category].append(t)

        # Select one from each category
        selected = []
        for category, trait_list in by_category.items():
            # Filter by difficulty modifier
            if difficulty == DifficultyLevel.BEGINNER:
                filtered = [t for t in trait_list if t.difficulty_modifier <= 1.0]
            elif difficulty == DifficultyLevel.EXPERT:
                filtered = [t for t in trait_list if t.difficulty_modifier >= 1.2]
            else:
                filtered = trait_list

            if filtered:
                selected.append(random.choice(filtered))

        return selected

    async def _select_objections(self, difficulty: DifficultyLevel) -> List[Objection]:
        """Select objections based on difficulty."""
        result = await self.db.execute(
            select(Objection).where(Objection.difficulty_level == difficulty)
        )
        matching = result.scalars().all()

        if not matching:
            # Fall back to all objections
            result = await self.db.execute(select(Objection))
            matching = result.scalars().all()

        if not matching:
            return []

        # Select 1-3 objections based on difficulty
        num_objections = {
            DifficultyLevel.BEGINNER: 1,
            DifficultyLevel.INTERMEDIATE: 2,
            DifficultyLevel.ADVANCED: 2,
            DifficultyLevel.EXPERT: 3,
        }.get(difficulty, 2)

        return random.sample(matching, min(num_objections, len(matching)))

    def _generate_name(self, gender: str) -> str:
        """Generate a first name."""
        names = FEMALE_NAMES if gender == "female" else MALE_NAMES
        return random.choice(names)

    def _generate_company_name(self, last_name: str, context: BusinessContext) -> str:
        """Generate a company name."""
        template = random.choice(COMPANY_TEMPLATES)
        trade_suffix = context.trade_name.replace("Contractor", "").strip()

        return template.format(
            last_name=last_name,
            trade=trade_suffix or context.trade_name,
            city=random.choice(CITIES),
            adjective=random.choice(ADJECTIVES),
        )

    def _generate_business_details(
        self,
        context: BusinessContext,
        difficulty: DifficultyLevel
    ) -> Dict[str, Any]:
        """Generate realistic business details."""
        # Revenue range based on difficulty (larger = more complex)
        revenue_ranges = {
            DifficultyLevel.BEGINNER: (150000, 400000),
            DifficultyLevel.INTERMEDIATE: (400000, 1500000),
            DifficultyLevel.ADVANCED: (1500000, 5000000),
            DifficultyLevel.EXPERT: (5000000, 20000000),
        }
        min_rev, max_rev = revenue_ranges.get(difficulty, (400000, 1500000))
        revenue = random.randint(min_rev // 10000, max_rev // 10000) * 10000

        # Employees based on revenue
        employees = max(1, revenue // 100000)

        # Years in business
        years = random.randint(2, 25)

        # Subcontractor usage
        uses_subs = context.subcontractor_usage and random.random() > 0.3

        return {
            "annual_revenue": revenue,
            "employees": employees,
            "years_in_business": years,
            "uses_subs": uses_subs,
            "operations": context.typical_operations or [],
            "equipment_heavy": context.equipment_intensive,
        }

    def _build_system_prompt(
        self,
        scenario: ScenarioTemplate,
        context: BusinessContext,
        name: str,
        company: str,
        business_details: Dict[str, Any],
        traits: List[PersonaTrait],
        objections: List[Objection],
    ) -> str:
        """Build the complete system prompt for Grok."""

        # Format traits
        trait_descriptions = []
        for t in traits:
            desc = f"- {t.name}: {t.description}"
            if t.behavioral_cues:
                desc += f"\n  Behaviors: {', '.join(t.behavioral_cues[:3])}"
            trait_descriptions.append(desc)

        # Format objections
        objection_instructions = []
        for o in objections:
            objection_instructions.append(
                f"- You will raise this objection: \"{o.objection_text}\""
            )

        # Format operations/risks
        operations = business_details.get("operations", context.typical_operations or [])
        risks = context.common_risks or []

        prompt = f"""You are {name}, the owner of {company}, a {context.trade_name.lower()} company.

## Your Business Profile
- Company: {company}
- Trade: {context.trade_name}
- Annual Revenue: ${business_details['annual_revenue']:,}
- Employees: {business_details['employees']}
- Years in Business: {business_details['years_in_business']}
- Uses Subcontractors: {"Yes" if business_details['uses_subs'] else "No"}
- Typical Operations: {', '.join(operations[:5]) if operations else 'General contracting work'}

## Your Personality Traits
{chr(10).join(trait_descriptions) if trait_descriptions else "- Professional and straightforward business owner"}

## Call Context
{scenario.base_prompt}

### Scenario Objectives (what the insurance agent should accomplish):
{chr(10).join('- ' + obj for obj in (scenario.objectives or ['Build rapport and understand your needs']))}

## Your Objections (you MUST raise these during the call)
{chr(10).join(objection_instructions) if objection_instructions else "- You have some price concerns but are open to discussion"}

## Important Guidelines
1. Stay in character as {name} throughout the entire conversation
2. Respond naturally as a real business owner would - you're busy and value your time
3. Don't be immediately cooperative - make the agent work to build rapport
4. Ask clarifying questions about coverage and pricing
5. Reference your specific business operations when discussing risks
6. If the agent handles your objections well, gradually become more receptive
7. If you're satisfied by the end, express interest in moving forward
8. Keep responses conversational - speak like a real contractor, not formally

## Common Industry Risks to Reference
{chr(10).join('- ' + r for r in risks[:5]) if risks else '- General liability concerns, workers comp issues, equipment damage'}

Remember: You are NOT an AI assistant. You are {name}, a real {context.trade_name.lower()} who has been contacted by an insurance agent. Respond only as {name} would."""

        return prompt
