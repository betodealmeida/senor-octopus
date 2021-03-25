from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union


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
