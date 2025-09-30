from typing import Optional
from pydantic import BaseModel, Field


class ServiceObject(BaseModel):
    id: Optional[int] = Field(description="Id услуги")
    service_name: Optional[str] = Field(description="имя услуги")
    service_price: Optional[float] = Field(description="цена услуги")
    quan: Optional[int] = Field(description="уникальный идентификатор")
