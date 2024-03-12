from fastapi import APIRouter, BackgroundTasks, status, HTTPException, Body, Depends, Query
from typing import Annotated
from bson import ObjectId
from config.db import extracted_collection
from schemas.extract_schema import extracts_serializer
from controllers.extractor import SentenceExtractor
from controllers.utils import Utils
from config.security import get_token, UnauthorizedMessage
from models.extract_model import ExtractorModel, CalendarInterval
import pymongo
import os, sys
from config.apm_client import client



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
            result = utils.get_sentence(sentence=body.sentence)
            if result['is_exist']:
                background_tasks.add_task(extracted_collection.update_one, filter = {
                    "_id": ObjectId(result['result']['id'])
                }, 
                update = {
                    "$set": {"counter": result['result']['counter'] + 1}
                })
                background_tasks.add_task(utils.update_counter_extracted, _id=result['result']['id'])
                return result['result']
            _id = extracted_collection.insert_one({**body.dict()})
            extracted = extracted_collection.find_one({"_id": _id.inserted_id})
            sentence_vector = st.extract(body.sentence).tolist()
            extracted = {**extracted, "sentence_vector": sentence_vector}
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
):
    try:
        if page_start < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page must be greater than or equal to 1",
            )
        
        skip_count = (page_start - 1) * page_size  # Adjust for 1-based indexing
        # Split the sort_by parameter into a list of sorting criteria
        sort_criteria = []
        if sort_by:
            sort_fields = sort_by.split(",")
            for field in sort_fields:
                direction = pymongo.ASCENDING
                if field.startswith('-'):
                    direction = pymongo.DESCENDING
                    field = field[1:]  # Remove the '-' prefix
                sort_criteria.append((field, direction))

    
        # Query MongoDB with skip, limit, sort, and projection
        extracted_cursor = extracted_collection.find({}).skip(skip_count).limit(page_size)
        # Check if sort_criteria is empty (default sort behavior)
        if not sort_criteria:
            extracted_cursor = extracted_cursor.sort([("_id", pymongo.DESCENDING)])  # Sort by _id in descending order by default
        else:
            extracted_cursor = extracted_cursor.sort(sort_criteria)
        # Serialize the results
        users = extracts_serializer(extracted_cursor)
        # Exclude specified fields from the output
        if exclude_fields:
            exclude_fields = exclude_fields.split(",")
            for user in users:
                for field in exclude_fields:
                    user.pop(field, None)
        # Calculate pagination metadata
        total_hits = extracted_collection.count_documents({})
        page_count = (total_hits + page_size - 1) // page_size  # Calculate pageCount
        page = page_start
        # Create the pagination metadata dictionary
        pagination = {
            "page": page,
            "pageSize": page_size,
            "pageCount": page_count,
            "total": total_hits
        }
        
        return {"status": True, "data": users, "meta": {"pagination": pagination}}
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
