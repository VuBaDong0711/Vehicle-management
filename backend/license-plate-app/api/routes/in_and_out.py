import asyncio
import base64
from enum import Enum
from typing import Union

from api.models.in_and_out import (InAndOutModelListOutV2, Search, SelectType, GetInOutForUser)
from api.models.check_exist_face import CheckExistFace, CheckExistFaceSchema
from fastapi import (APIRouter, BackgroundTasks, File, Form, Query,Depends,
                     UploadFile, WebSocket, Request)
from api.models.vehicle import VehicleType

from fastapi.responses import StreamingResponse
from utils.pyobjectid import PyObjectId

from api.schemas.check_in_and_out import CheckInAndOutSchema

from api.controllers.controller import *
from core.jwt import get_current_user



router = APIRouter(prefix='/in_and_out',tags=['In and out'],responses={'404':{'description': 'Not found'}})

@router.post('/check_image')
async def check_image(image: UploadFile):
    data = base64.b64encode(image.file.read())
    test = await inAndOutCtrl.predict(data)
    return test

@router.post('/turn_in_out')
async def turn_in_out(
    task: BackgroundTasks,
    image: UploadFile=File(...),
    id_region:PyObjectId=Form(...),
    select_turn: SelectType = Form(...),
    vehicle_type: VehicleType = Form(...)
):
    image_base64 = base64.b64encode(image.file.read())
    plates_json = await inAndOutCtrl.predict(image_base64)
    data = await inAndOutCtrl.check_vehicle(
        plates_json,
        id_region,
        select_turn.value,
        vehicle_type.value,
        task
    )
    return data

@router.post('/check_turn_in_out')
async def check_turn_in_out(
    task: BackgroundTasks,
    check: CheckInAndOutSchema
):
    check = check.dict()
    data = await inAndOutCtrl.check_vehicle_v2(
        check['plates'],
        check['id_region'],
        check['turn']
    )
    return data

@router.post('/check_turn_in_out_realtime/one_object')
async def check_turn_in_out_realtime(
    check: CheckInAndOutSchema
):
    '''
    kiểm tra turn in out biển số xe trong thời gian thực
    '''
    # check.plate, check.id_region = "49E1-22222", '633eab6969d18929cf048b83'
    check = check.dict()
    data = await inAndOutCtrl.check_vehicle_realtime_for_one_user(
        plates_json=check['plates'], 
        id_region=check['id_region'], 
        turn=check['turn'],
        vehicle_img_base64=check['image_base64']
    )
    return data

@router.post('/mark_face')
async def mark_face(
    check: CheckExistFaceSchema
):
    '''
    Đánh dấu mặt trong mongodb (có thời gian lưu 120 giây, sau đó tự động xóa)
    '''
    data = await inAndOutCtrl.add_username_to_exist_face(
        check.username, 
        check.id_region, 
        check.image_base64
        )
    return {"detail": "marked"}

# @router.post('/check_turn_in_out_realtime')
# async def check_turn_in_out_realtime(
#     check: CheckInAndOutSchema
# ):
#     check = check.dict()
#     data = await inAndOutCtrl.check_vehicle_realtime_for_one_user(
#         plates_json=check['plates'], 
#         id_region=check['id_region'], 
#         turn=check['turn'])
#     return data

class SortDates(str, Enum):
    ascending = 'date'
    descending = '-date'

@router.post('/search_in_and_out',response_model=InAndOutModelListOutV2)
async def get_all_in_and_out_time(
    order: Union[SortDates,None]=None,
    search: Union[Search,None]=None,
    page: int = Query(0, ge=0),
    limit: int = Query(20, ge=0, le=50),
):
    '''
    tìm kiếm số lượng xe ra vào theo search
    '''
    sort = None
    if order is not None:
        sort = 1 if order == SortDates.ascending else -1
    data = await inAndOutCtrl.get_aggregate(sort,page,limit,search)
    return data

@router.post('/get_detail_in_and_out_for_user',response_model=InAndOutModelListOutV2)
async def get_all_in_and_out_time(
    order: Union[SortDates,None]=None,
    search: Union[GetInOutForUser,None]=None,
    page: int = Query(0, ge=0),
    limit: int = Query(20, ge=0, le=50),
    current_user=Depends(get_current_user)
):
    '''
    Lấy thông tin ra vào của user đó theo thời gian cho trước
    '''
    sort = None
    if order is not None:
        sort = 1 if order == SortDates.ascending else -1
    data = await inAndOutCtrl.get_aggregate_user(sort,page,limit,search,current_user['id'])
    return data


@router.get('/statistic_in_and_out')
async def statistic_in_and_out(date: str):
    '''
    Thống kê số lượng xe ra vào
    '''
    return await inAndOutCtrl.statistic_in_and_out(date)