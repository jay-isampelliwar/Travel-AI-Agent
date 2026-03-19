from langchain_openai import ChatOpenAI


class LLM:
    _instance = None

    def __new__(cls, model_name: str = "gpt-4o-mini"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.llm = ChatOpenAI(model=model_name)
        return cls._instance.llm
