from pydantic import BaseModel, Field
from typing import List


class QueryGeneratorModel(BaseModel):
    queries: List[str] = Field(description="List of queries used to travel journeys")

    def to_dict(self):
        return {"queries": self.queries}

