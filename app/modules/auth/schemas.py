from pydantic import BaseModel, ConfigDict, Field


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        validation_alias="idToken",
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        min_length=1,
        validation_alias="refreshToken",
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    firstName: str | None = None
    lastName: str | None = None
    username: str
    picture: str | None = None


class GoogleLoginResponse(BaseModel):
    user: UserResponse
    access_token: str = Field(..., serialization_alias="accessToken")
    refresh_token: str = Field(..., serialization_alias="refreshToken")
    access_token_expires_in: int = Field(
        ...,
        serialization_alias="accessTokenExpiresIn",
    )
    refresh_token_expires_in: int = Field(
        ...,
        serialization_alias="refreshTokenExpiresIn",
    )