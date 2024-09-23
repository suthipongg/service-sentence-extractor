from fastapi import APIRouter, BackgroundTasks, status, Body, Depends, Query
from typing import Annotated
from bson import ObjectId

from configs.db import MGCollection, ESIndex
from configs.security import get_token, UnauthorizedMessage
from controllers.extractor import SentenceExtractor
from controllers.mongodb_controller import MGFuncs
from controllers.elasticsearch_controller import ESFuncs
from models.extract_model import ExtractorModel, ExtractorListModel
from models.report_model import BodyList
from request_examples.get_list import getList
from schemas.extract_schema import extract_serializer_list, extract_serializer

extractor_route = APIRouter(tags=["Sentence Extractor"])


@extractor_route.post(
        "/extractor/model",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def embedded_model(
    body: ExtractorListModel,
    token_auth: str = Depends(get_token),
):
    vectors = SentenceExtractor().extract(body.sentences)
    return {"vector": vectors}


@extractor_route.post(
        "/extractor/elasticsearch/multiple",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def multiple_sentence_embedding(
    body: ExtractorListModel,
    token_auth: str = Depends(get_token),
):
    results = [None] * len(body.sentences)
    new_setences = {}
    for n, sentence in enumerate(body.sentences):
        is_exist, source = ESFuncs.check_sentence_exists(ESIndex.EXTRACTED, sentence)
        if is_exist:
            results[n] = source['sentence_vector']
        else:
            new_setences[n] = sentence
    vect_new_sentences = (await embedded_model(body=ExtractorListModel(sentences=list(new_setences.values()))))['vector']
    for n, new_vect in zip(list(new_setences.keys()), vect_new_sentences):
        results[n] = new_vect
    return {"result": results}


@extractor_route.post(
        "/extractor/elasticsearch/single",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def single_sentence_embedding(
    body: ExtractorModel,
    token_auth: str = Depends(get_token),
):
    is_exist, source = ESFuncs.check_sentence_exists(ESIndex.EXTRACTED, body.sentence)
    if is_exist:
        return {"is_exist": True, "result": source}
    else:
        vector_response = await embedded_model(body=ExtractorListModel(sentences=body.sentence))
        return {"is_exist": False, "result": vector_response['vector'][0]}


@extractor_route.post(
        "/extractor",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def extractor_sentence(
    body: ExtractorModel,
    background_tasks: BackgroundTasks,
    token_auth: str = Depends(get_token),
):
    sentence_vector = await single_sentence_embedding(body=ExtractorModel(sentence=body.sentence))
    if sentence_vector['is_exist']:
        sentence_vector['result']['counter'] += 1
        background_tasks.add_task(
            MGCollection.EXTRACTED.update_one, 
            filter = {"_id": ObjectId(sentence_vector['result']['id'])}, 
            update = {"$set": {"counter": sentence_vector['result']['counter']}}
        )

        background_tasks.add_task(
            ESFuncs.update_counter,
            index_name=ESIndex.EXTRACTED,
            id=sentence_vector['result']['id']
        )
        return sentence_vector['result']
    
    body: dict = body.model_dump()
    _id = MGCollection.EXTRACTED.insert_one(body.copy())
    body['sentence_vector'] = sentence_vector['result']
    body['id'] = str(_id.inserted_id)
    ESFuncs.insert_es(ESIndex.EXTRACTED, body, id=body['id'])
    return body

@extractor_route.get(
        "/extractor/model/warmup",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def embedded_model_warmup(
    token_auth: str = Depends(get_token),
):
    SentenceExtractor().extract('สวัสดีครับ')
    return {"detail": "success"}


@extractor_route.post(
        "/extractor/getList",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def extractor_get_list(
    body: Annotated[
            BodyList,
            Body(
                openapi_examples=getList
            )
        ],
    token_auth: str = Depends(get_token),
):
    items, pagination = MGFuncs.query_collection(body, MGCollection.EXTRACTED)
    return {
        "status": True, 
        "data": extract_serializer_list(items), 
        "meta": {"pagination": pagination}
    }

@extractor_route.get(
        "/extractor/{id}",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def get_one_extracted(
    id: str,
    token_auth: str = Depends(get_token)
):
    extracted = extract_serializer(MGCollection.EXTRACTED.find_one({"_id": ObjectId(id)}))
    if extracted:
        return {"status": True,"data": extracted}
    else:
        return {"status": False, "detail": "Item not found."}
    

@extractor_route.delete(
        "/extractor/{id}",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def delete_extractor(
    id: str,
    background_tasks: BackgroundTasks,
    token_auth: str = Depends(get_token)
):
    data = MGCollection.EXTRACTED.find_one({"_id": ObjectId(id)})
    if data:
        MGCollection.EXTRACTED.delete_one(filter={"_id": ObjectId(id)})
        ESFuncs.delete_es(index_name=ESIndex.EXTRACTED, id=id)
        return {"status": True, "data": extract_serializer(data)}
    else:
        return {"status": False, "detail": "Item not found."}

