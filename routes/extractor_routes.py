from fastapi import APIRouter, BackgroundTasks, status, HTTPException, Body, Depends, Query
from typing import Annotated
from bson import ObjectId
from config.db import extracted_collection
from schemas.extract_schema import extracts_serializer
from controllers.extractor import SentenceExtractor
from controllers.utils import Utils
from config.security import get_token, UnauthorizedMessage
from models.extract_model import ExtractorModel, CalendarInterval, BodyList, ExtractorListModel
import os, sys
from config.apm_client import client
from controllers.utils_pymongo import parse_sort_criteria, parse_filter_criteria, apply_sort
from request_examples.get_list import getList
from typing import Annotated


print('Sentence Extractor Loading :::')
st = SentenceExtractor()
print('Sentence Extractor Start :::')

utils = Utils()
extractor_model = APIRouter(tags=["SentenceE Extractor"])

@extractor_model.post(
        "/extractor",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def extractor(
    body: ExtractorModel,
    background_tasks: BackgroundTasks,
    token_auth: str = Depends(get_token),
):
    try:
        if body.sentence:
            sentence_vector = await embedded_model(body=body)
            if sentence_vector['is_exist']:
                background_tasks.add_task(extracted_collection.update_one, filter = {
                    "_id": ObjectId(sentence_vector['result']['id'])
                }, 
                update = {
                    "$set": {"counter": sentence_vector['result']['counter'] + 1}
                })
                background_tasks.add_task(utils.update_counter_extracted, _id=sentence_vector['result']['id'])
                return sentence_vector['result']
            _id = extracted_collection.insert_one({**body.dict()})
            extracted = extracted_collection.find_one({"_id": _id.inserted_id})
            extracted = {**extracted, "sentence_vector": sentence_vector['sentence_vector']}
            # Convert _id to string
            extracted = {'id' if k == '_id' else k: str(v) if k == '_id' else v for k, v in extracted.items()}

            background_tasks.add_task(utils.bulk_extracted, datas=[extracted])
            return extracted
        else:
            raise HTTPException(status_code=400, detail="sentence not provided.")
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:  
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  

@extractor_model.post(
        "/extractor/model",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def embedded_model(
    body: ExtractorModel,
    token_auth: str = Depends(get_token),
):
    try:
        result = utils.get_sentence(sentence=body.sentence)
        if result['is_exist']:
            return result
        sentence_vector = st.extract(body.sentence).tolist()
        return {"is_exist": False, "sentence_vector": sentence_vector}
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:  
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  

@extractor_model.get(
        "/extractor/model/warmup",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def embedded_model_warmup(
    token_auth: str = Depends(get_token),
):
    try:
        st.extract('สวัสดีครับ')
        return {"message": "success"}
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:  
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  

@extractor_model.post(
        "/extractor/tokenizer/counter",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def tokenizer_counter(
    body: ExtractorListModel,
    token_auth: str = Depends(get_token),
):
    try:
        counts = [len(tk) for tk in st.tokenizer(body.sentences)["input_ids"]]
        return {"success": True, "token_count": counts}
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:  
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  


@extractor_model.get(
        "/extractor",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def find_all_extracted(
    token_auth: str = Depends(get_token),
    page_start: int = Query(default=1, description="Starting page number"),
    page_size: int = Query(default=10, description="Number of items per page"),
    exclude_fields: str = Query(
        default="",
        description="Comma-separated list of fields to exclude from the output",
    ),
    sort_by: str = Query(
        default="",
        description="Comma-separated list of fields to sort by (e.g., 'field1,-field2' for descending)",
    ),
    filter: str = Query(
        default="",
        description="Filter criteria (e.g., 'field1:value1,field2:*value2*')",
    ),
):
    try:
        if page_start < 1:
            raise HTTPException(
                status_code=400,
                detail="Page must be greater than or equal to 1",
            )

        skip_count = (page_start - 1) * page_size

        # Parse the sort_by string into sorting criteria
        sort_criteria = parse_sort_criteria(sort_by)

        # Parse the filter string into filter criteria
        if filter:
            filter_criteria = {"$and":  parse_filter_criteria(filter)}
        else:
            filter_criteria = {}

        # Query MongoDB with sorting and filtering
        extracted_cursor = extracted_collection.find(filter_criteria)
        # extracted_cursor = sentence_extracted_collection.find(filter_criteria)
        extracted_cursor = apply_sort(extracted_cursor, sort_criteria)
        extracted_cursor = extracted_cursor.skip(skip_count).limit(page_size)

        # Serialize the results
        extracted_list = extracts_serializer(extracted_cursor)

        # Exclude specified fields from the output
        if exclude_fields:
            exclude_fields = exclude_fields.split(",")
            for doc in extracted_list:
                for field in exclude_fields:
                    doc.pop(field, None)

        # Calculate pagination metadata
        total_hits = extracted_collection.count_documents(filter_criteria)
        # total_hits = sentence_extracted_collection.count_documents(filter_criteria)
        page_count = (total_hits + page_size - 1) // page_size
        pagination = {
            "page": page_start,
            "pageSize": page_size,
            "pageCount": page_count,
            "total": total_hits
        }

        return {"status": True, "data": extracted_list, "meta": {"pagination": pagination}}
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()  
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  
    
@extractor_model.get(
        "/extractor/report",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def extractor_report(
            start_date: str = Query(
                default = utils.first_day.strftime("%Y-%m-%dT00:00:00"),
                description = "Filter start datetime"
            ),
            end_date: str = Query(
                default = utils.last_day.strftime("%Y-%m-%dT23:59:59"),
                description = "Filter start datetime"
            ),
            calendar_interval: CalendarInterval = Query(
                default= "day",
                description="Calendar Interval"
            ),
            token_auth: str = Depends(get_token),
        ):
    try:

        result = utils.group_by_sentence({"start_date": start_date, "end_date": end_date, "type": "setting", "calendar_interval":calendar_interval.value})
        return result
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:  
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()  
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  
    

@extractor_model.get(
        "/extractor/{id}",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def get_one_extracted(
    id: str,
    token_auth: str = Depends(get_token)
    ):
    try:
        extracted = extracts_serializer(extracted_collection.find({"_id": ObjectId(id)}))
        if extracted:
            return {"status": True,"data": extracted[0]}
        else:
            raise HTTPException(status_code=404, detail="Item not found.")
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
    

@extractor_model.delete(
        "/extractor/{id}",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def delete_extractor(
    id: str,
    background_tasks: BackgroundTasks,
    token_auth: str = Depends(get_token)
    ):
    try:
        background_tasks.add_task(extracted_collection.delete_one, filter={"_id": ObjectId(id)})
        background_tasks.add_task(utils.delete_extracted, _id=id)

        return {"status": True, "data": {}}
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


@extractor_model.post(
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
    try:
        items, pagination = await utils.filter_collection(body, extracted_collection)
        return {"status": True, "data": extracts_serializer(items), "meta": {"pagination": pagination}}
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:  
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()  
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  