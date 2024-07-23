from pydantic import BaseModel
from datetime import datetime

class TokenizerModel(BaseModel):
    text: str = ''
    created_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        self.created_at = datetime.now()

    class Config:
        json_schema_extra = {
            "example": {
                "text": "สวัสดีครับผม",
            }
        }
    
