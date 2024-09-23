from fastapi import APIRouter, status, Depends

from configs.security import get_token, UnauthorizedMessage
from controllers.extractor import SentenceExtractor
from models.extract_model import ExtractorListModel

tokenizer_route = APIRouter(tags=["Sentence Tokenizer"])


@tokenizer_route.post(
        "/tokenizer/counter",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def tokenizer_counter(
    body: ExtractorListModel,
    token_auth: str = Depends(get_token),
):
    counts = SentenceExtractor().compute_token(body.sentences)
    return {"success": True, "token_count": counts}