from fastapi import APIRouter, status, HTTPException, Depends
from config.security import get_token, UnauthorizedMessage
import os, sys
from config.apm_client import client
from controllers.utils import Utils
from models.tokenizer_model import TokenizerModel



utils = Utils()

tokenizer_model = APIRouter(tags=["Sentence Tokenizer"])


@tokenizer_model.get(
        "/tokenizer/train",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def tokenizer_train(
    token_auth: str = Depends(get_token)
):
    try:
        result = await utils.get_trainnlu_datas()
        return {"status": True, "result": result}
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()  
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  
    

@tokenizer_model.post(
        "/tokenizer",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def tokenizer(
    body: TokenizerModel,
    token_auth: str = Depends(get_token)
):
    try:
        if body.text:
            result = await utils.ngrams(body.text.strip())
            return {"status": True, "result": result}
        raise HTTPException(status_code=400, detail="text not provided.")
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()  
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  
