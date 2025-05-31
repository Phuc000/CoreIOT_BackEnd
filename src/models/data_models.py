from pydantic import BaseModel

class DataModel(BaseModel):
    id: int
    name: str
    value: float

class ResponseModel(BaseModel):
    success: bool
    message: str
    data: DataModel = None