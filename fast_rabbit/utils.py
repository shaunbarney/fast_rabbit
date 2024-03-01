import json
from pydantic import BaseModel

from typing import Any


def serialise_data(data: Any) -> str:
    """Serializes data to a JSON string, handling Pydantic models and other types."""
    if isinstance(data, BaseModel):
        return data.json()
    elif isinstance(data, (dict, list)):
        return json.dumps(data)
    else:
        return str(data)
