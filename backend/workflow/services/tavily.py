from langchain_tavily import TavilySearch


class TavilySearchService:
    _instance = None

    def __new__(cls, max_results: int = 5):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.search = TavilySearch(max_results=max_results)
        return cls._instance.search
