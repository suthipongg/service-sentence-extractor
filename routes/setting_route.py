from fastapi import APIRouter, status, Depends, HTTPException, Body

from config.security import UnauthorizedMessage, get_token
from config.apm_client import client
import os, json, sys
from dotenv import load_dotenv, dotenv_values, set_key
load_dotenv()

setting_route = APIRouter(tags=["SETTINGS"])

@setting_route.post(
    "/setting/environment/reload", 
    responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
    status_code=status.HTTP_200_OK,
)
async def reload_env(
    token_auth: str = Depends(get_token)
):  
    try:
        load_dotenv('config/.env.shared', override=True)
        return {"env": dotenv_values("config/.env.shared"), "detail": "sync environment success"}
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:  
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()  
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  


@setting_route.get(
    "/setting/environment/display", 
    responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
    status_code=status.HTTP_200_OK,
)
async def display_env(
    env_fields: str,
    token_auth: str = Depends(get_token)
):  
    try:
        await reload_env(token_auth)
        env_info = dotenv_values("config/.env.shared")
        if env_fields:
            env_info = {env_field.strip():os.getenv(env_field.strip()) for env_field in env_fields.split(",") if env_field.strip() in env_info}
        return {"env": env_info, "detail": "get environment success"}
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:  
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()  
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  


@setting_route.post(
    "/setting/environment/set",
    responses={status.HTTP_401_UNAUTHORIZED: dict(model=UnauthorizedMessage)},
    status_code=status.HTTP_200_OK,
)
async def set_env(
    dc_env: dict = Body(...), 
    token_auth: str = Depends(get_token)
):  
    try:
        await reload_env(token_auth)
        key_env = dotenv_values("config/.env.shared")
        result = {"success": {}, "fail": {}}
        for key, val in dc_env.items():
            try:
                if key in key_env:
                    val = str(val)
                    result["success"][key] = val
                        
                    set_key("config/.env.shared", key, val)
                    os.environ[key] = val
                else:
                    result["fail"][key] = "not found"
            except Exception as e:
                result["fail"][key] = str(e)
        return {"env": result, "detail": "set environment success"}
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:  
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        client.capture_exception()  
        raise HTTPException(status_code=500, detail="Internal Server Error") from e  
