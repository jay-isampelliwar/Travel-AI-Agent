from typing import List, Literal, Optional

from langchain.tools import tool
from pydantic import BaseModel, Field, validator


class DayPlan(BaseModel):
    """Single day in an itinerary."""

    day: int = Field(..., description="Day number starting from 1")
    theme: str = Field(..., description="High-level theme or focus for the day")
    morning: str = Field(..., description="Morning activities and suggestions")
    afternoon: str = Field(..., description="Afternoon activities and suggestions")
    evening: str = Field(..., description="Evening activities and suggestions")
    notes: Optional[str] = Field(
        None, description="Optional tips, reservations, or flexibility notes"
    )


class ItineraryInput(BaseModel):
    """Strict inputs for itinerary generation."""

    destination: str = Field(..., description="Destination city or region, e.g. 'Paris'")
    days: int = Field(..., ge=1, le=30, description="Trip length in days (1–30)")
    interests: List[
        Literal[
            "culture",
            "history",
            "food",
            "nightlife",
            "shopping",
            "nature",
            "beach",
            "family",
            "adventure",
            "relaxation",
        ]
    ] = Field(
        default_factory=list,
        description=(
            "Top interests to prioritize. "
            "Use the fixed vocabulary: culture, history, food, nightlife, "
            "shopping, nature, beach, family, adventure, relaxation."
        ),
    )

    @validator("destination")
    def _strip_destination(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Destination cannot be empty.")
        return v


class ItineraryOutput(BaseModel):
    """Structured itinerary returned as JSON."""

    destination: str
    days: int
    primary_interests: List[str]
    overview: str
    day_plans: List[DayPlan]
    tips: List[str]


def _normalize_interests(interests: List[str]) -> List[str]:
    """Normalize free-form interests into our controlled vocabulary."""
    if not interests:
        return ["culture", "food"]

    mapping = {
        "museum": "culture",
        "art": "culture",
        "architecture": "culture",
        "heritage": "history",
        "historical": "history",
        "gastronomy": "food",
        "restaurant": "food",
        "bar": "nightlife",
        "club": "nightlife",
        "shopping": "shopping",
        "hike": "nature",
        "mountain": "nature",
        "park": "nature",
        "sea": "beach",
        "coast": "beach",
        "kids": "family",
        "children": "family",
        "theme park": "family",
        "extreme": "adventure",
        "sports": "adventure",
        "spa": "relaxation",
    }

    normalized: List[str] = []
    for raw in interests:
        key = raw.strip().lower()
        if key in mapping.values():
            normalized.append(key)
            continue
        # fuzzy mapping by keyword containment
        matched = None
        for pattern, target in mapping.items():
            if pattern in key:
                matched = target
                break
        normalized.append(matched or "culture")

    # Deduplicate while preserving order
    seen = set()
    ordered: List[str] = []
    for item in normalized:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered or ["culture", "food"]


def _build_day_theme(day_index: int, days: int, interests: List[str]) -> str:
    """Heuristic day theme selection."""
    primary = interests[day_index % len(interests)]
    if days <= 3:
        return f"Highlights of {primary}"
    if day_index == 0:
        return "Orientation & city highlights"
    if day_index == days - 1:
        return "Relaxed finale & last-minute favorites"
    return f"Deep dive into {primary}"


def _segment_text(destination: str, theme: str, interest: str, segment: str) -> str:
    """Template text for a given day-part."""
    base = f"In {destination}, focus on {interest}."
    if segment == "morning":
        return (
            f"{base} Start with a relaxed breakfast near your accommodation, then explore "
            f"a landmark area that fits the theme: think guided walking tour or self-guided "
            f"stroll aligned with '{theme.lower()}'."
        )
    if segment == "afternoon":
        return (
            f"{base} After lunch, plan a main activity block: book one key attraction or experience "
            f"that strongly matches '{interest}', and leave a short buffer for spontaneous stops."
        )
    return (
        f"{base} For the evening, choose a restaurant that reflects local cuisine, then consider "
        f"a low-effort activity such as a sunset viewpoint, riverfront walk, or casual bar that "
        f"matches the '{theme.lower()}' vibe."
    )


@tool(
    "generate_itinerary",
    args_schema=ItineraryInput,
    description=(
        "Generate a structured, day-by-day travel itinerary JSON for a destination based on trip "
        "duration and top traveler interests. Use when the user wants a clear daily plan with "
        "morning/afternoon/evening suggestions and high-level themes, not specific ticket links."
    ),
)
def generate_itinerary(
    destination: str, days: int, interests: Optional[List[str]] = None
) -> dict:
    """Generate a structured itinerary as JSON for downstream consumption."""

    interests_list = interests or []

    print(
        f"\033[38;5;208m>>> [TOOL START] generate_itinerary: "
        f"{destination} for {days} days, interests={interests_list}\033[0m"
    )

    try:
        input_model = ItineraryInput(
            destination=destination,
            days=days,
            interests=interests_list,
        )
    except Exception as e:
        # Fall back to a minimal but valid structure on validation errors
        print(
            f"\033[38;5;208m>>> [TOOL WARN] itinerary input validation failed: {e}\033[0m"
        )
        normalized_interests = _normalize_interests(interests_list)
        output = ItineraryOutput(
            destination=destination.strip() or destination,
            days=max(1, min(days or 1, 30)),
            primary_interests=normalized_interests,
            overview=(
                "Basic itinerary generated with relaxed pacing and flexible activities. "
                "Inputs were partially invalid, so defaults were applied."
            ),
            day_plans=[
                DayPlan(
                    day=1,
                    theme="Flexible highlights",
                    morning=_segment_text(destination, "Orientation", normalized_interests[0], "morning"),
                    afternoon=_segment_text(
                        destination, "Flexible exploration", normalized_interests[0], "afternoon"
                    ),
                    evening=_segment_text(
                        destination, "Relaxed evening", normalized_interests[0], "evening"
                    ),
                    notes="Validate dates, reservations, and opening hours before booking.",
                )
            ],
            tips=[
                "Double-check opening hours and reservation policies before finalizing bookings.",
                "Group nearby sights on the same day to reduce transit time.",
            ],
        )
        return output.model_dump()

    normalized_interests = _normalize_interests(input_model.interests)

    day_plans: List[DayPlan] = []
    for idx in range(input_model.days):
        day_num = idx + 1
        interest = normalized_interests[idx % len(normalized_interests)]
        theme = _build_day_theme(idx, input_model.days, normalized_interests)

        notes: Optional[str] = None
        if day_num == 1:
            notes = (
                "Keep the schedule slightly lighter to account for travel fatigue. "
                "Avoid locking in non-refundable activities on arrival day."
            )
        elif day_num == input_model.days:
            notes = (
                "Leave buffer in the afternoon/evening for packing, airport/train transfers, "
                "and any last-minute shopping."
            )

        day_plans.append(
            DayPlan(
                day=day_num,
                theme=theme,
                morning=_segment_text(input_model.destination, theme, interest, "morning"),
                afternoon=_segment_text(input_model.destination, theme, interest, "afternoon"),
                evening=_segment_text(input_model.destination, theme, interest, "evening"),
                notes=notes,
            )
        )

    overview = (
        f"{input_model.days}-day itinerary for {input_model.destination} focused on "
        f"{', '.join(normalized_interests[:3])}"
        f"{' and more' if len(normalized_interests) > 3 else ''}. "
        "Days are paced to balance structured activities with flexibility and downtime."
    )

    tips = [
        "Front-load must-see experiences earlier in the trip in case of weather or disruptions.",
        "Cluster activities by neighborhood to minimize transit time and backtracking.",
        "For popular attractions, pre-book timed-entry tickets where possible.",
        "Always keep one backup indoor and one outdoor activity per day for flexibility.",
    ]

    output = ItineraryOutput(
        destination=input_model.destination,
        days=input_model.days,
        primary_interests=normalized_interests,
        overview=overview,
        day_plans=day_plans,
        tips=tips,
    )

    print(
        f"\033[38;5;208m>>> [TOOL INFO] Generated itinerary for {input_model.destination} "
        f"({input_model.days} days, interests={normalized_interests})\033[0m"
    )
    return output.model_dump()
