=============
senor-octopus
=============

Señor Octopus is a streaming hub, fetching data from APIs, transforming it, filtering it, and storing it, based on a declarative configuration.

Confused? Keep reading.

A simple example
================

Señor Octopus reads a pipeline definition from a YAML configuration file like this:

.. code-block:: yaml

    # generate random numbers and send them to "check" and "normal"
    random:
      plugin: source.random
      flow: -> check, normal
      schedule: "* * * * *"  # every minute

    # filter numbers from "random" that are > 0.5 and send to "high"
    check:
      plugin: filter.jsonpath
      flow: random -> high
      filter: "$.events[?(@.value>0.5)]"

    # log all the numbers coming from "random" at the default level
    normal:
      plugin: sink.log
      flow: "* ->"
      batch: 5 minutes

    # log all the numbers coming from "check" at the warning level
    high:
      plugin: sink.log
      flow: check ->
      level: warning

The example above has a **source** called "random", that generates random numbers every minute (its ``schedule``). It's connected to 2 other nodes, "check" and "normal" (``flow = -> check, normal``). Each random number is sent in an **event** that looks like this:

.. code-block:: json

    {
        "timestamp": "2021-01-01T00:00:00+00:00",
        "name": "hub.random",
        "value": 0.6394267984578837
    }

The node ``check`` is a **filter** that verifies that the value of each number is greater than 0.5. Events that pass the filter are sent to the ``high`` node (the filter connects the two nodes, according to ``flow = random -> high``).

The node ``normal`` is a **sink** that logs events. It receives events from any other node (``flow = * ->``), and stores them in a queue, logging them at the ``INFO`` level (the default) every 5 minutes (``batch = 5 minutes``). The node ``high``, on the other hand, receives events only from ``check``, and logs them immediately at the ``WARNING`` level.

To run it:

.. code-block:: bash

    $ srocto config.yaml -vv
    [2021-03-25 14:28:26] INFO:senor_octopus.cli:Reading configuration
    [2021-03-25 14:28:26] INFO:senor_octopus.cli:Building DAG
    [2021-03-25 14:28:26] INFO:senor_octopus.cli:
    *   random
    |\
    * | check
    | * normal
    * high

    [2021-03-25 14:28:26] INFO:senor_octopus.cli:Running Sr. Octopus
    [2021-03-25 14:28:26] INFO:senor_octopus.scheduler:Starting scheduler
    [2021-03-25 14:28:26] INFO:senor_octopus.scheduler:Scheduling random to run in 33.76353 seconds
    [2021-03-25 14:28:26] DEBUG:senor_octopus.scheduler:Sleeping for 5 seconds

To stop running, press ``ctrl+C``. Any batched events will be processed before the scheduler terminates.

A concrete example
==================

Now for a more realistic example. I wanted to monitor the air quality in my bedroom, using an `Awair Element <https://www.getawair.com/home/element>`_. Since their API is throttled I want to read values once every 5 minutes, and store everything in a Postgres database. If the CO2 value is higher than 1000 ppm I want to receive a notification on my phone, limited to one message every 30 minutes.

This is the config I use for that:

.. code-block:: yaml

    awair:
      plugin: source.awair
      flow: -> *
      schedule: "*/5 * * * *"
      prefix: hub.awair
      access_token: XXX
      device_type: awair-element
      device_id: 12345
      
    high_co2:
      plugin: filter.jsonpath
      flow: awair -> pushover
      filter: '$.events[?(@.name=="hub.awair.co2" and @.value>1000)]'
      
    pushover:
      plugin: sink.pushover
      flow: high_co2 ->
      throttle: 30 minutes
      app_token: XXX
      user_token: johndoe
      
    db:
      plugin: sink.db.postgresql
      flow: "* ->"
      batch: 15 minutes
      dbname: dbname
      user: user
      password: password
      host: host
      port: 5432

I'm using `Pushover <https://pushover.net/>`_ to send notifications to my phone.

Will it rain?
=============

Here's another example, a pipeline that will notify you if tomorrow will rain:

.. code-block:: yaml

    weather:
      plugin: source.weatherapi
      flow: -> will_it_rain
      schedule: 0 12 * * *
      location: London
      access_token: XXX

    will_it_rain:
      plugin: filter.jsonpath
      flow: weather -> pushover
      filter: '$.events[?(@.name=="hub.weatherapi.forecast.forecastday.daily_will_it_rain" and @.value==1)]'

    pushover:
      plugin: sink.pushover
      flow: will_it_rain ->
      throttle: 30 minutes
      app_token: XXX
      user_token: johndoe

Event-driven sources
====================

Señor Octopus also supports event-driven sources. Differently to the sources in the previous examples, these sources run constantly and respond immediately to events. An example is the `MQTT <https://mqtt.org/>`_ source:

.. code-block:: yaml

    mqtt:
      plugin: source.mqtt
      flow: -> log
      topics: test/#
      host: mqtt.example.org

    log:
      plugin: sink.log
      flow: mqtt ->

Running the pipeline above, when an event arrives in the MQTT topic ``test/#`` (eg, ``test/1``) it will be immediately sent to the log.

There's also an MQTT sink, that will publish events to a given topic:

.. code-block:: yaml

    mqtt:
      plugin: sink.mqtt
      flow: "* ->"
      topic: test/1
      host: mqtt.example.org
