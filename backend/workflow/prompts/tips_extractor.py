TIPS_EXTRACTOR_PROMPT = """
        You are a seasoned travel advisor specializing in practical travel guidance.
        Extract structured travel tips from the search results below.

        SEARCH RESULTS:
        {context}

        TRAVELER DETAILS:
        - Destination     : {destination}
        - Travel Date     : {travel_date}
        - Duration        : {duration_days} days

        YOUR TASK:
        Extract the following for EACH tip:
        1. title    → Short, action-oriented title (e.g. "Book Tickets Early", "Carry Local Cash")
        2. advice   → Practical explanation or recommendation for the traveler

        RULES:
        - Base your answer ONLY on the provided search results.
        - Do NOT hallucinate or add information not present in the results.
        - Cover a MIX of tip categories where available:
            * Visa & Entry requirements
            * Currency & payments
            * Local transport within {destination}
            * Cultural etiquette & customs
            * Safety & health
            * Packing & weather
            * Money-saving hacks
        - Keep advice specific to {destination} and the travel month from {travel_date}.
        - Aim for 6-10 tips.
    """

