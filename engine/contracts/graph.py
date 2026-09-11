from dataclasses import dataclass, field

@dataclass
class Param:
    """A single parameter of a function or method."""
    name: str
    default: str | None = None
    position: int = 0

@dataclass
class Node:
    """A single entity of code which can be a function, method, class or module."""
    id: str
    type: str                                                   #Function/method/class/module
    name: str
    file: str                                                   #relative file path where its defined
    line: int                                                   #Line number in that file
    signature: str = ""
    params: list[Param] = field(default_factory=list)
    is_public: bool = True                                      #False for names starting with '_'

@dataclass
class Edge:
    """A relationship between two nodes/entities."""
    from_id: str
    to_id: str
    type: str                                                   #calls/inherits/imports/overrides

@dataclass
class Graph:
    """The full semantic/context graph for one version of one framework."""
    framework: str
    version: str
    nodes: dict[str, Node] = field(default_factory=dict)        #keyed by node ID
    edges: list[Edge] = field(default_factory=list)