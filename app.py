print('start project chat bot Sentence Extractor ::: ')
from fastapi import FastAPI, Request
import time
import datetime
from config.middleware import log_request_middleware

from elasticapm.contrib.starlette import ElasticAPM
from elasticapm import set_context
from starlette.requests import Request
from elasticapm.utils.disttracing import TraceParent
from config.apm_client import client
from fastapi.middleware.cors import CORSMiddleware


ALLOWED_ORIGINS = ['*']


# # ---- Deployment UAT - PROD 
# app = FastAPI(
#     title="Project Chat AI: Sentence Extractor API (2023)", 
#     description=f"Created by zax \n TNT Media and Network Co., Ltd. \n Started at {datetime.datetime.now().strftime('%c')}", 
#     root_path="/extractor", 
#     docs_url="/",
#     version="1.0.0",
# )


app = FastAPI(
    title="Project Chat AI: Sentence Extractor API (2023)", 
    description=f"Created by zax \n TNT Media and Network Co., Ltd. \n Started at {datetime.datetime.now().strftime('%c')}",
    docs_url="/",
    version="1.0.0",
    )

app.add_middleware(  
    CORSMiddleware,  
    allow_origins=ALLOWED_ORIGINS,  # Allows CORS for this specific origin  
    allow_credentials=True,  
    allow_methods=["*"],  # Allows all methods  
    allow_headers=["*"],  # Allows all headers  
)  

apm = ElasticAPM(app, client=client)

  
@app.middleware("http")  
async def add_process_time_header(request: Request, call_next):  
    trace_parent = TraceParent.from_headers(request.headers)  
    client.begin_transaction('request', trace_parent=trace_parent)  
    set_context({  
        "method": request.method,  
        "url_path": request.url.path,  
    }, 'request')  
    response = await call_next(request)  
    set_context({  
        "status_code": response.status_code,  
    }, 'response')  
    # Check if the status code is not in the range of 200-299  
    if 200 <= response.status_code < 300:  
        transaction_status = 'success'  
    else:  
        transaction_status = 'failure'  
    client.end_transaction(f'{request.method} {request.url.path}', transaction_status)  
    return response  


app.middleware("http")(log_request_middleware)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = "{0:.2f}ms".format(process_time)
    return response


from routes.tokenizer_routes import tokenizer_model
app.include_router(tokenizer_model)

from routes.extractor_routes import extractor_model
app.include_router(extractor_model)

