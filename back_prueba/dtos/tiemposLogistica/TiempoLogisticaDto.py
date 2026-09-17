from pydantic import BaseModel
from typing import Optional

class ReporteFiltrosRequest(BaseModel):
    sucursal_id: Optional[int] = None
    prioridad: Optional[str] = None
    estado: Optional[str] = None