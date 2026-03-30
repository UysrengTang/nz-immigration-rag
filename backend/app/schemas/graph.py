from pydantic import Field

from app.schemas.answer import AnswerDraft, FinalResponse
from app.schemas.common import BaseSchema
from app.schemas.retrieval import EvidenceSufficiency, RetrievalFilters, RetrievedChunk


class GraphState(BaseSchema):
    request_id: str
    user_query: str
    rewritten_query: str | None = None
    normalized_query: str | None = None
    user_intent_flags: list[str] = Field(default_factory=list)
    retrieval_filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    expanded_chunks: list[RetrievedChunk] = Field(default_factory=list)
    reranked_chunks: list[RetrievedChunk] = Field(default_factory=list)
    selected_evidence: list[RetrievedChunk] = Field(default_factory=list)
    sufficiency: EvidenceSufficiency | None = None
    answer_draft: AnswerDraft | None = None
    final_response: FinalResponse | None = None
    refusal_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)
    trace_tags: dict[str, object] = Field(default_factory=dict)
