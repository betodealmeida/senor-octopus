=============
senor-octopus
=============

Señor Octopus is a streaming hub, fetching data from APIs, transforming it, filtering it, and storing it, based on a declarative configuration.

Confused? Keep reading.

A simple example
================

Señor Octopus reads a pipeline defintion from a configuration file like this:

.. code-block:: ini

    # generate random numbers and send them to "check" and "normal"
    [random]
    plugin = source.random
    flow = -> check, normal
    schedule = * * * * *

    # filter numbers from "random" that are > 0.5 and send to "high"
    [check]
    plugin = filter.jsonpath
    flow = random -> high
    filter = $.events[?(@.value>0.5)]

    # log all the numbers coming from "random" at the default level
    [normal]
    plugin = sink.log
    flow = * ->
    batch = 5 minutes

    # log all the numbers coming from "check" at the warning level
    [high]
    plugin = sink.log
    flow = check ->
    level = warning

The example above has a **source** called "random", that generates random numbers every minute (its ``schedule``). It's connected to 2 other nodes, "check" and "normal" (``flow = -> check, normal``). Each random number is an **event** that looks like this:

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

    $ srocto config.ini -vv
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

A concrete example
==================

Now for a more realistic example. I wanted to monitor the air quality in my bedroom, using an `Awair Element <https://www.getawair.com/home/element>`_. Since their API is throttled I want to read values once every 5 minutes, and store everything in a Postgres database. If the CO2 value is higher than 1000 ppm I want to receive a notification on my phone, limited to one message every 30 minutes.

This is the config I use for that:

.. code-block:: ini

    [awair]
    plugin = source.awair
    flow = -> *
    schedule = */5 * * * *
    prefix = hub.awair
    AWAIR_ACCESS_TOKEN = XXX
    AWAIR_DEVICE_TYPE = awair-element
    AWAIR_DEVICE_ID = 12345
    
    [high_co2]
    plugin = filter.jsonpath
    flow = awair -> pushover
    filter = $.events[?(@.name=="hub.awair.co2" and @.value>1000)]
    
    [pushover]
    plugin = sink.pushover
    flow = high_co2 ->
    throttle = 30 minutes
    PUSHOVER_APP_TOKEN = XXX
    PUSHOVER_USER_TOKEN = johndoe
    
    [db]
    plugin = sink.db.postgresql
    flow = * ->
    batch = 15 minutes
    POSTGRES_DBNAME = dbname
    POSTGRES_USER = user
    POSTGRES_PASSWORD = password
    POSTGRES_HOST = host
    POSTGRES_PORT = 5432

I'm using `Pushover <https://pushover.net/>`_ to send notifications to my phone.

Will it rain?
=============

Here's another example, a pipeline that will notify you if tomorrow will rain:

.. code-block:: ini

    [weather]
    plugin = source.weatherapi
    flow = -> will_it_rain
    schedule = 0 12 * * *
    location = London
    WEATHERAPI_TOKEN = XXX

    [will_it_rain]
    plugin = filter.jsonpath
    flow = weather -> pushover
    filter = $.events[?(@.name=="hub.weatherapi.forecast.forecastday.daily_will_it_rain" and @.value==1)]

    [pushover]
    plugin = sink.pushover
    flow = will_it_rain ->
    throttle = 30 minutes
    PUSHOVER_APP_TOKEN = XXX
    PUSHOVER_USER_TOKEN = johndoe
