from io import StringIO
from typing import Any
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple
from typing import Union

import asciidag.graph
import asciidag.node
from senor_octopus.graph import Node
from senor_octopus.graph import Source


def flatten(
    obj: Dict[str, Any],
    prefix: str = "",
    sep: str = ".",
) -> Dict[str, Union[str, int, float]]:
    items: List[Tuple[str, Union[str, int, float]]] = []
    for key, value in obj.items():
        new_key = sep.join((prefix, key)) if prefix else key
        if isinstance(value, dict):
            items.extend(flatten(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def render_dag(dag: Set[Source], **kwargs: Any) -> str:
    out = StringIO()
    graph = asciidag.graph.Graph(out, **kwargs)
    tips = sorted(build_asciidag(node) for node in dag)

    graph.show_nodes(tips)
    out.seek(0)
    return out.getvalue()


def build_asciidag(node: Node) -> asciidag.node.Node:
    asciidag_node = asciidag.node.Node(node.name)
    asciidag_node.parents = sorted(
        [build_asciidag(child) for child in node.next],
        key=lambda n: n.item,
    )
    return asciidag_node
