from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CharacterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    current_state: str
    identity_label: str
    accepted_signal_count: int
    total_signal_count: int
    forge_days: int
    forge_state: str
    forge_cooling: bool
    today_alignment: int
    is_active: bool
    is_dev: bool = False
    created_at: datetime


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str | None
    is_active: bool
    is_dev: bool = False
    created_at: datetime
    active_character: CharacterResponse | None = None
