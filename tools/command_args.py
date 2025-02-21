# tools/common_args.py
import argparse

def get_common_parser(include_port: bool = False) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Galago Tools Manager",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with detailed logging'
    )
    if include_port:
        parser.add_argument(
            '--port',
            required=True,
            help='Port number for the tool server'
        )
    return parser
