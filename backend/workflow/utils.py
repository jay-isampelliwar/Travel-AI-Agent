from datetime import datetime

def get_current_date_time() -> str:
    return datetime.now().strftime("%A, %B %d, %Y %I:%M %p")

def format_search_results(search_results : list) -> str:
    formatted = []
    for i, result in enumerate(search_results, 1):
        if isinstance(result, dict):
            formatted.append(
                f"[Source {i}]: {result.get('title', 'No Title')}\n"
                f"URL: {result.get('url', '')}\n"
                f"Content: {result.get('content', result.get('snippet', ''))}\n"
            )
        else:
            # result is a plain string
            formatted.append(f"[Source {i}]: {result}\n")
    return "\n---\n".join(formatted)