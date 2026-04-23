from typing import List, Optional

from pydantic import BaseModel


class OrgTemplateSettingOut(BaseModel):
    """One template's enabled or disabled status for an organization."""

    template_id: str
    template_name: str
    subject: str
    is_active: bool
    is_enabled: bool

    class Config:
        from_attributes = True


class OrgTemplateSettingUpdate(BaseModel):
    is_enabled: bool


class OrgTemplateBulkUpdate(BaseModel):
    is_enabled: bool
    template_ids: Optional[List[str]] = None
