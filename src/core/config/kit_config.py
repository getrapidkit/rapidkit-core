# src / core / config / kit_config.py
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class VariableType(Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    LIST = "list"
    CHOICE = "choice"


@dataclass
class Variable:
    name: str
    type: VariableType
    required: bool = False
    default: Any = None
    description: str = ""
    choices: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Variable":
        return cls(
            name=data["name"],
            type=VariableType(data.get("type", "string")),
            required=data.get("required", False),
            default=data.get("default"),
            description=data.get("description", ""),
            choices=data.get("choices", []),
        )


@dataclass
class StructureItem:
    path: str
    template: Optional[str] = None
    template_if: Optional[Dict[str, str]] = field(default_factory=dict)
    content: Optional[str] = None
    modules: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StructureItem":
        return cls(
            path=data["path"],
            template=data.get("template"),
            template_if=data.get("template_if", {}),
            content=data.get("content"),
            modules=data.get("modules", []),
            conditions=data.get("conditions", {}),
        )


@dataclass
class KitConfig:
    name: str
    display_name: str
    description: str
    version: str
    min_rapidkit_version: str
    category: str
    tags: List[str]
    dependencies: Dict[str, Any]
    modules: List[str]
    variables: List[Variable]
    structure: List[StructureItem]
    hooks: Dict[str, str]
    path: Optional[Path] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KitConfig":
        variables = [
            Variable.from_dict({**var_data, "name": name})
            for name, var_data in data.get("variables", {}).items()
        ]

        structure = [StructureItem.from_dict(item) for item in data.get("structure", [])]

        return cls(
            name=data["name"],
            display_name=data["display_name"],
            description=data["description"],
            version=data["version"],
            min_rapidkit_version=data["min_rapidkit_version"],
            category=data["category"],
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", {}),
            modules=data.get("modules", []),
            variables=variables,
            structure=structure,
            hooks=data.get("hooks", {}),
        )
