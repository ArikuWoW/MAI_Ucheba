from typing import List
from pydantic import BaseModel


class User(BaseModel):
    id: int
    f_name: str
    l_name: str
    login: str
    password: str
    
class Report(BaseModel):
    id: int
    title: str
    description: str
    author_id: int
    
class Conference(BaseModel):
    id: int
    name: str
    reports: List[int] = []



