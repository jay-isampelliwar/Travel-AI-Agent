TIMING_EXTRACTOR_PROMPTS = """
        You are a travel expert specializing in seasonal travel patterns.
        Extract structured travel timing information from the search results below.

        SEARCH RESULTS:
        {context}

        TRAVELER DETAILS:
        - Destination     : {destination}
        - Travel Date     : {travel_date}
        - Duration        : {duration_days} days

        YOUR TASK:
        Extract the following:
        1. best_time_to_visit     → Best months or season to visit {destination}
        2. peak_season_benefits   → Key experiences ONLY available during peak season
        3. off_season_benefits    → Advantages of visiting during off-season (cheaper, less crowded, etc.)
        4. missed_benefits_off_season → What travelers MISS if they visit outside the best season

        RULES:
        - Base your answer ONLY on the provided search results.
        - Do NOT hallucinate or add information not present in the results.
        - Be specific to {destination}, not generic travel advice.
        - Keep each point concise (1-2 sentences max).
    """

