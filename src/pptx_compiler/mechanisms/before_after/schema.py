from pydantic import BaseModel, ConfigDict, Field


class BeforeAfterParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    before: list[str] = Field(default_factory=list)
    after: list[str] = Field(default_factory=list)
    keep: list[str] = Field(default_factory=list)
