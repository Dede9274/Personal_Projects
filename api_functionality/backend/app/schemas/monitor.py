"""Request and response schemas for the monitor API."""

from collections.abc import Mapping
from datetime import datetime
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    model_validator,
)


MonitorName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=255,
    ),
]
PositiveInterval = Annotated[int, Field(gt=0)]
PositiveTimeout = Annotated[
    float,
    Field(gt=0, allow_inf_nan=False),
]
HttpStatusCode = Annotated[int, Field(ge=100, le=599)]


class MonitorCreate(BaseModel):
    """Data accepted when a monitor is created."""

    model_config = ConfigDict(extra="forbid")

    name: MonitorName
    url: HttpUrl
    interval_seconds: PositiveInterval
    timeout_seconds: PositiveTimeout
    expected_status_code: HttpStatusCode = 200
    is_active: bool = True


class MonitorUpdate(BaseModel):
    """Fields that can be changed with a PATCH request."""

    model_config = ConfigDict(extra="forbid")

    name: MonitorName | None = None
    url: HttpUrl | None = None
    interval_seconds: PositiveInterval | None = None
    timeout_seconds: PositiveTimeout | None = None
    expected_status_code: HttpStatusCode | None = None
    is_active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_patch_body(cls, data: Any) -> Any:
        """Require at least one change and disallow explicit null values."""
        if not isinstance(data, Mapping):
            return data

        if not data:
            raise ValueError("At least one field must be provided")

        null_fields = sorted(
            field_name
            for field_name, value in data.items()
            if value is None
        )

        if null_fields:
            fields = ", ".join(null_fields)
            raise ValueError(f"Fields cannot be null: {fields}")

        return data


class MonitorRead(BaseModel):
    """Complete monitor representation returned by the API."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: int
    name: str
    url: HttpUrl
    interval_seconds: int
    timeout_seconds: float
    expected_status_code: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
