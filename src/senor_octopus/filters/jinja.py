import logging

from jinja2 import Template
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def jinja(stream: Stream, template: str) -> Stream:
    """
    Apply a Jinja2 template to events.

    This filter can be used to transform events according to
    a template, or filter them (templates that return nothing
    filter out the corresponding event).

    Parameters
    ----------
    stream
        The incoming stream of events
    template
        A Jinja2 template

    Yields
    ------
    Event
        Events filtered and/or transformed by the template
    """
    _logger.debug("Applying template to events")
    tmpl = Template(template)
    async for event in stream:  # pragma: no cover
        value = tmpl.render(event=event).strip()
        if value:
            yield {
                "timestamp": event["timestamp"],
                "name": event["name"],
                "value": value,
            }
