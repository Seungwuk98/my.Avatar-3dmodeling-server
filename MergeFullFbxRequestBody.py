from pydantic import BaseModel

class Config(BaseModel):
    x : float
    y : float
    z : float
    s : float

class MergeFullFbxRequestBody(BaseModel):
    head_url : str
    body_url : str
    hair_url : str
    body_config : Config
    hair_config : Config
    