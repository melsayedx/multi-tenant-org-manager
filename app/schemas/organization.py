from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.membership import Role


class OrgCreate(BaseModel):
    org_name: str = Field(min_length=1, max_length=64)


class OrgResponse(BaseModel):
    org_id: UUID


class InviteUser(BaseModel):
    email: EmailStr
    role: Role


class InviteResponse(BaseModel):
    message: str


class UserInOrg(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class PaginatedUsers(BaseModel):
    users: list[UserInOrg]
    total: int
    limit: int
    offset: int
