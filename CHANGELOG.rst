=========
Changelog
=========

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
