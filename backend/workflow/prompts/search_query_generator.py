SEARCH_QUERY_GENERATOR_PROMPT = """
You are a travel research assistant. Generate exactly 6 search queries for:
- Source: {source}
- Destination: {destination}  
- Travel Date: {travel_date}
- Duration: {duration_days} days

Return ONLY a JSON array of 6 strings covering these topics in order:
1. Best time to visit {destination} in [month from {travel_date}]
2. How to travel from {source} to {destination}
3. Top things to do in {destination} in {duration_days} days
4. {destination} weather packing guide [month from {travel_date}]
"""

