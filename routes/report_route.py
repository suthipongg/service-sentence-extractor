from fastapi import APIRouter, status, Depends, Query

from datetime import datetime, timedelta

from configs.security import get_token, UnauthorizedMessage
from configs.db import ESIndex
from controllers.mongodb_controller import MGFuncs
from controllers.elasticsearch_controller import ESFuncs
from controllers.extractor import SentenceExtractor
from models.report_model import CalendarInterval

report_route = APIRouter(tags=["Report"])


@report_route.get(
        "/report/extractor",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
async def extractor_report(
    start_date: str = Query(
        default = datetime.now().replace(day=1).strftime("%Y-%m-%dT00:00:00"),
        description = "Filter start datetime"
    ),
    end_date: str = Query(
        default = (datetime.now().replace(month=datetime.now().month+1).replace(day=1)  - timedelta(days=1)).strftime("%Y-%m-%dT23:59:59"),
        description = "Filter start datetime"
    ),
    calendar_interval: CalendarInterval = Query(
        default= "day",
        description="Calendar Interval"
    ),
    token_auth: str = Depends(get_token),
):
    result = ESFuncs.aggregate_sentence_total_by_days(
        ESIndex.EXTRACTED, 
        {
            "start_date": start_date, 
            "end_date": end_date, 
            "type": "setting", 
            "calendar_interval":calendar_interval.value
        }
    )
    return result
    

@report_route.get(
        "/report/dependency",
        responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
        )
def check_dependency(token_auth: str = Depends(get_token)):
    mg_connected = MGFuncs.check_mongo_connection()
    es_connected = ESFuncs.check_elasticsearch_connection()
    apm_connected = ESFuncs.check_apm_connection()
    st_started = SentenceExtractor._instance is not None
    return {
        "status": {
            "mongodb": "connected" if mg_connected else "disconnected",
            "elasticsearch": "connected" if es_connected else "disconnected",
            "apm": "connected" if apm_connected else "disconnected",
            "sentence_extractor": "started" if st_started else "stopped",
        }
    }