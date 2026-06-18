from fastapi import APIRouter, Request

from app.schemas.request import QuestionRequest
from app.schemas.response import QuestionResponse

from app.services.rag_service import RAGService


router = APIRouter()

rag = RAGService()


@router.post(
    "/ask",
    response_model=QuestionResponse
)
def ask_question(
    request: Request,
    body: QuestionRequest
):
    tracer = request.state.tracer

    result = rag.ask(
        question=body.question,
        tracer=tracer,
    )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "metrics": result["metrics"],
    }