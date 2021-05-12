=============
senor-octopus
=============

They say there are only 2 kinds of work: you either move information from one place to another, or you move mass from one place to another.

**Señor Octopus is an application that moves data around**. It reads a YAML configuration file that describes how to connect **nodes**. For example, you might want to measure your internet speed every hour and store it in a database:

.. code-block:: yaml

    speedtest:
      plugin: source.speedtest
      flow: -> db
      schedule: @hourly

    db:
      plugin: sink.db.postgresql
      flow: speedtest ->
      user: alice
      password: XXX
      host: localhost
      port: 5432
      dbname: default
      
Nodes are connected by the ``flow`` attribute. The ``speedtest`` node is connected to the ``db`` node because it points to it:

.. code-block:: yaml

    speedtest:
      flow: -> db

The ``db`` node, on the other hand, listens to events from the ``speedtest`` node:

.. code-block:: yaml

    db:
      flow: speedtest ->

We can also use ``*`` as a wildcard, if we want a node to connect to all other nodes, or specify a list of nodes:

.. code-block:: yaml

    speedtest:
      flow: -> db, log
      
    db:
      flow: "* ->"
      
Note that in YAML we need to quote attributes that start with an asterisk.

Running Señor Octopus
=====================

You can save the configuration above to a file called ``speedtest.yaml`` and run:

.. code-block:: bash

    $ pip install senor-octopus
    $ srocto speedtest.yaml

Every hour the ``speedtest`` **source** node will run, and the results will be sent to the ``db`` **sink** node, which writes them to a Postgres database.

How to these results look like?

Events
======

Señor Octopus uses a very simple but flexible data model to move data around. We have nodes called **sources** that create a stream of events, each one like this:

.. code-block:: python

    class Event(TypedDict):
        timestamp: datetime
        name: str
        value: Any
    
An event has a **timestamp** associated with it, a **name**, and a **value**. Note that the value can be anything!

A **source** will produce a stream of events. In the example above, once per hour the ``speedtest`` source will produce events like these:

.. code-block:: python

    [
        {
            'timestamp': datetime.datetime(2021, 5, 11, 22, 16, 26, 812083, tzinfo=datetime.timezone.utc),
            'name': 'hub.speedtest.download',
            'value': 16568200.018792046,
        },
        {
            'timestamp': datetime.datetime(2021, 5, 11, 22, 16, 26, 812966, tzinfo=datetime.timezone.utc),
            'name': 'hub.speedtest.upload',
            'value': 5449607.159468643,
        },
        {
            'timestamp': datetime.datetime(2021, 5, 11, 22, 16, 26, 820369, tzinfo=datetime.timezone.utc),
            'name': 'hub.speedtest.client',
            'value': {
                'ip': '173.211.12.32',
                'lat': '37.751',
                'lon': '-97.822',
                'isp': 'Colocation America Corporation',
                'isprating': '3.7',
                'rating': '0',
                'ispdlavg': '0',
                'ispulavg': '0',
                'loggedin': '0',
                'country': 'US',
            }
        },
        ...
    ]

The events are sent to **sinks**, which consume the stream. In this example, the ``db`` sink will receive the events and store them in a Postgres database.

Event-driven sources
====================

In the previous example we configured the ``speedtest`` source to run hourly. Not all sources need to be scheduled, though. We can have a source that listens to a given topic in `MQTT <https://mqtt.org/>`_, eg:

.. code-block:: yaml

    mqtt:
      plugin: source.mqtt
      flow: -> db
      topics:
        - "srocto/feeds/#"
      host: localhost
      port: 1883
      username: bob
      password: XXX
      message_is_json: true

The source above will immediately send an event to the ``db`` node every time a new message shows up in the topic wildcard ``srocto/feeds/#``, so it can be written to the database — a super easy way of persisting a message queue to disk!

Batching events
===============

The example above is not super efficient, since it writes to the database every time an event arrives. Instead, we can easily **batch** the events so that they're accumulated in a queue and processed every, say, 5 minutes:

.. code-block:: yaml

    db:
      plugin: sink.db.postgresl
      flow: speedtest, mqtt ->
      batch: 5 minutes
      user: alice
      password: XXX
      host: localhost
      port: 5432
      dbname: default

With the ``batch`` parameter any incoming events are stored in a queue for the configured time, and processed by the sink together. Any pending events in the queue will still be processed if ``srocto`` terminates gracefully (eg, with ``ctrl+C``).

Filtering events
================

Much of the flexibility of Señor Octopus comes from a third type of node, the **filter**. Filters can be used to not only filter data, but also format it. For example, let's say we want to turn on some lights at sunset. The ``sun`` source will send events with a value of "sunset" or "sunrise" every time one occurs:

.. code-block:: python

    {
        'timestamp': ...,
        'name': 'hub.sun',
        'value': 'sunset',
    }

The ``tuya`` sink can be used to control a smart switch, but in order to turn it on it expects an event that looks like this:

.. code-block:: python

    {
        'timestamp': ...,
        'name': ...,
        'value': 'on',
    }

We can use the ``jinja`` filter to ignore "sunrise" events, and to convert the "sunset" value into "on":


.. code-block:: yaml

    sun:
      plugin: source.sun
      flow: -> sunset
      latitude: 38.3
      longitude: -123.0

    sunset:
      plugin: filter.jinja
      flow: sun -> lights
      template: >
        {% if event['value'] == 'sunset' %}
          on
        {% endif %}

    lights:
      plugin: sink.tuya
      flow: sunset ->
      device: "Porch lights"
      email: charlie@example.com
      password: XXX
      country: "1"
      application: smart_life

With this configuration the ``sunset`` filter will drop any events that don't have a value of "sunset". And for those events that have, the value will be replaced by the string "on" so it can activate the lights in the ``lights`` node.

Throttling
==========

Sometimes we want to limit the number of events being consumed by a sink. For example, imagine that we want to use Señor Octopus to monitor air quality using an `Awair Element <https://www.getawair.com/home/element>`_, sending us an SMS when the score is below a given threshold. We would like the SMS to be sent at most once every 30 minutes, and only between 8am and 10pm.

Here's how we can do that:

.. code-block:: yaml

    awair:
      plugin: source.awair
      flow: -> bad_air
      schedule: 0/10 * * * *
      access_token: XXX
      device_type: awair-element
      device_id: 12345
    
    bad_air:
      plugin: filter.jinja
      flow: awair -> sms
      template: >
        {% if
           event['timestamp'].astimezone().hour >= 8 and
           event['timestamp'].astimezone().hour <= 21 and
           event['name'] == 'hub.awair.score' and
           event['value'] < 80
        %}
          Air quality score is low: {{ event['value'] }}
        {% endif %}
    
    sms:
      plugin: sink.sms
      flow: bad_air ->
      throttle: 30 minutes
      account_sid: XXX
      auth_token: XXX
      from: "+18002738255"
      to: "+15558675309"

In the example above, the ``awair`` source will fetch air quality data every 10 minutes, and send it to ``bad_air``. The filter checks for the hour, to prevent sending an SMS from 10pm to 8am, and checks the air quality score — if it's lower than 80 it will reformat the value of the event to a nice message, eg:

    "Air quality score is low: 70"

This is then sent to the ``sms`` sink, which has a ``throttle`` of 30 minutes. The throttle configuration will prevent the sink from running more than once every 30 minutes, to avoid spamming us with messages in case the score remains low.

Plugins
=======

Señor Octopus supports an increasing list of plugins, and it's straightforward to add new ones. Each plugin is simply a function that produces, processes, or consumes a stream.

Here's the ``random`` source, which produces random numbers:

.. code-block:: python

    async def rand(events: int = 10, prefix: str = "hub.random") -> Stream:
        for _ in range(events):
            yield {
                "timestamp": datetime.now(timezone.utc),
                "name": prefix,
                "value": random.random(),
            }

This is the full source code for the ``jinja`` filter:

.. code-block:: python

    async def jinja(stream: Stream, template: str) -> Stream:
        _logger.debug("Applying template to events")
        tmpl = Template(template)
        async for event in stream:
            value = tmpl.render(event=event)
            if value:
                yield {
                    "timestamp": event["timestamp"],
                    "name": event["name"],
                    "value": value,
                }

And this is the ``sms`` sink:

.. code-block:: python

    async def sms(
        stream: Stream, account_sid: str, auth_token: str, to: str, **kwargs: str
    ) -> None:
        from_ = kwargs["from"]
        client = Client(account_sid, auth_token)
        async for event in stream:
            _logger.debug(event)
            _logger.info("Sending SMS")
            client.messages.create(body=str(event["value"]).strip(), from_=from_, to=to)

As you can see, a source is an async generator that yields events. A filter receives the stream with additional configuration parameters, and also returns a stream. And a sink receives a stream with additional parameters, and returns nothing.

Sources
~~~~~~~

The current plugins for sources are:

- `source.awair <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sources/awair.py>`_: Fetch air quality data from Awair Element monitor.
- `source.crypto <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sources/crypto.py>`_: Fetch price of cryptocurrencies from cryptocompare.com.
- `source.mqtt <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sources/mqtt.py>`_: Subscribe to messages on one or more MQTT topics.
- `source.rand <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sources/rand.py>`_: Generate random numbers between 0 and 1.
- `source.speed <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sources/speed.py>`_: Measure internet speed.
- `source.sqla <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sources/sqla.py>`_: Read data from database.
- `source.static <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sources/static.py>`_: Generate static events.
- `source.stock <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sources/stock.py>`_: Fetch stock price form Yahoo! Finance.
- `source.sun <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sources/sun.py>`_: Send events on sunrise and sunset.
- `source.weatherapi <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sources/weatherapi.py>`_: Fetch weather forecast data from weatherapi.com.
- `source.whistle <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sources/whistle.py>`_: Fetch device information and location for a Whistle pet tracker.

Filters
~~~~~~~

The existing filters are very similar, the main difference being how you configure them:

- `filter.format <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/filters/format.py>`_: Format an event stream based using Python string formatting.
- `filter.jinja <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/filters/jinja.py>`_: Apply a Jinja2 template to events.
- `filter.jsonpath <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/filters/jpath.py>`_: Filter event stream based on a JSON path.

Sinks
~~~~~

These are the current sinks:

- `sink.log <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sinks/log.py>`_: Send events to a logger.
- `sink.mqtt <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sinks/mqtt.py>`_: Send events as messages to an MQTT topic.
- `sink.pushover <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sinks/pushover.py>`_: Send events to the Pushover mobile app.
- `sink.sms <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sinks/sms.py>`_: Send SMS via Twilio.
- `sink.tuya <https://github.com/betodealmeida/senor-octopus/blob/main/src/senor_octopus/sinks/tuya.py>`_: Send commands to a Tuya/Smart Life device.
