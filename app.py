from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from elasticapm import set_context
from elasticapm.contrib.starlette import ElasticAPM
from elasticapm.utils.disttracing import TraceParent

import time, datetime

from configs.logger import LoggerConfig
from configs.exception_handler import custom_exception_handler
from configs.middleware import log_all_request_middleware

LoggerConfig.logger.info('\033[92mStart project chat bot Sentence Extractor\033[0m ::: ')

from configs.config import SettingsManager
SettingsManager.initialize()

from configs.es_model import ElasticsearchIndexConfigs
ElasticsearchIndexConfigs()

from configs.db import (
    MongoDBConnection, MGCollection,
    ElasticsearchConnection, ESIndex
)
MongoDBConnection.connect_mongodb()
MGCollection.init_collection()
ElasticsearchConnection.connect_elasticsearch()
apm_client = ElasticsearchConnection.connect_apm_service()
ESIndex.init_index()

from controllers.elasticsearch_controller import ESFuncs
ESFuncs.start_index_es()

from controllers.extractor import SentenceExtractor
SentenceExtractor.init_instance()

ALLOWED_ORIGINS = ['*']


app = FastAPI(
    title="Project Chat AI: Sentence Extractor API (2023)", 
    description=f"Created by zax \n TNT Media and Network Co., Ltd. \n Started at {datetime.datetime.now().strftime('%c')}",
    docs_url="/",
    version="1.0.0",
    debug=False
)

app.add_exception_handler(Exception, custom_exception_handler)

app.add_middleware(  
    CORSMiddleware,  
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,  
    allow_methods=["*"],
    allow_headers=["*"],
)  

apm = ElasticAPM(app, client=apm_client)
  
@app.middleware("http")  
async def add_process_apm_service(request: Request, call_next):  
    trace_parent = TraceParent.from_headers(request.headers)  
    apm_client.begin_transaction('request', trace_parent=trace_parent)  
    set_context({  
        "method": request.method,  
        "url_path": request.url.path,  
    }, 'request')  
    response = await call_next(request)  
    set_context({  
        "status_code": response.status_code,  
    }, 'response')  
    
    if 200 <= response.status_code < 300:  
        transaction_status = 'success'  
    else:  
        transaction_status = 'failure'  
    apm_client.end_transaction(f'{request.method} {request.url.path}', transaction_status)  
    return response  

app.middleware("http")(log_all_request_middleware)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = "{0:.2f}ms".format(process_time)
    return response


from routes.extractor_route import extractor_route
app.include_router(extractor_route)

from routes.tokenizer_route import tokenizer_route
app.include_router(tokenizer_route)

from routes.report_route import report_route
app.include_router(report_route)

LoggerConfig.logger.info('\033[92mStarted project chat bot Sentence Extractor\033[0m ::: ')