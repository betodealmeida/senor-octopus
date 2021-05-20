=========
Changelog
=========

Version 0.1.14 - 2021-05-20
===========================

- New filter: Jinja2 template
- New sink: Twilio SMS
- MQTT source now reconnects

Version 0.1.13 - 2021-05-10
===========================

- Handle JSON-encoded MQTT messages
- Fix throttle by ignoring runs without events
- Log exceptions

Version 0.1.12 - 2021-05-08
===========================

- New sources: suntime, static
- New sink: Tuya/Smart Life
- Format plugin parameters simplified
- Fix jsonpath filter to work with event streams

Version 0.1.11 - 2021-05-05
===========================

- Switch config to YAML
- Log all events flowing in the DAG
- Add docstrings to all plugins for API generation
- New filter: format
- New source: SQLAlchemy databases
- Fix schedule with only event sources
- Fix multiple topics in mqtt source

Version 0.1.10 - 2021-03-29
===========================

- Modified scheduler to run tasks concurrently 
- Modified scheduler to gracefully cancel tasks
- Added support for event-driven sources (non-scheduled)
- New sources: Whistle, stocks, crypto, mqtt
- New sink: mqtt

Version 0.1.9 - 2021-03-25
==========================

- Add missing dependency to setup.py

Version 0.1.8 - 2021-03-25
==========================

- Render DAG after building it

Version 0.1.7 - 2021-03-25
==========================

- Add more logging

Version 0.1.6 - 2021-03-25
==========================

- Fix DAG builder n:1 relationships

Version 0.1.5 - 2021-03-25
==========================

- New source: Weatherapi
- Improved scheduler

Version 0.1.4 - 2021-03-23
==========================

- Implement batch in sinks

Version 0.1.3 - 2021-03-23
==========================

- Group tasks with a tolerance in scheduler
- Prevent failed tasks from stopping scheduler

Version 0.1.2 - 2021-03-23
==========================

- Add missing entry point to Speedtest source

Version 0.1.1 - 2021-03-23
==========================

- Fix typos in README.rst
- Add missing dependency
- New source: Speedtest

- Initial release
Version 0.1 - 2021-03-23
========================

- Initial release
- Sources: Awair, random numbers
- Filters: JSONPath
- Sinks: Pushover, Postgres, logs
