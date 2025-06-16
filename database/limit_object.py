import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LimitObject(BaseModel):
    """
    Объект лимита для логирования

    param id: id ивента
    param type: Тип лимита(daily/extra)
    param post_id: ID вакансии привязанной к лимиту
    param user_id: Id владельца лимита
    param: status: Какое действие проведено с данным лимитом(added/deleted/returned)
    param created_at: Время данного ивента
    """
    id: Optional[int] = Field(None,description="id ивента")
    type: Optional[str] = Field(description="Тип лимита(daily/extra)")
    post_id: Optional[int] = Field(description="ID вакансии привязанной к лимиту")
    user_id: Optional[int] = Field(description="Id владельца лимита")
    status: Optional[str] = Field(description="Какое действие проведено с данным лимитом(added/deleted/returned)")
    created_at:Optional[datetime.datetime] = Field(None,description="Время данного ивента")