import argparse
import configparser
import logging
import sys

from senor_octopus import __version__
from senor_octopus.graph import build_dag
from senor_octopus.scheduler import Scheduler

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version="senor-octopus {ver}".format(ver=__version__),
    )
    parser.add_argument(
        dest="f",
        help="Location of the config file",
        type=str,
        metavar="PATH",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel,
        stream=sys.stdout,
        format=logformat,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class CaseConfigParser(configparser.RawConfigParser):
    def optionxform(self, optionstr):
        return optionstr


def main(args):
    args = parse_args(args)
    setup_logging(args.loglevel)

    _logger.info("Reading configuration...")
    config = CaseConfigParser()
    config.read(args.f)
    dag = build_dag(config)

    _logger.info("Running Sr. Octopus...")
    Scheduler(dag).run()

    _logger.info("Done")


def run():
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
