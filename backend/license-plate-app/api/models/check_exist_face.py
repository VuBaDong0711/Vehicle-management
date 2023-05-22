from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from base.models import BaseModel
from base.schema import IDSchema, PaginationInfo
from pydantic import EmailStr, Field,AnyUrl
from utils.pyobjectid import ObjectId, PyObjectId
from api.models.entrance_auth import EntranceAuthModel

class CheckExistFace(BaseModel):
    username: Optional[str]
    id_region: Optional[PyObjectId]
    created_at: Optional[datetime]