#!/usr/bin/env python3
"""
echo.py - Simple echo action for testing the dispatcher system

This action echoes back the provided arguments, making it ideal for
testing the command dispatcher without side effects.
"""

import argparse


def main(args: list[str] | None = None) -> None:
    """Echo the provided message with optional formatting."""
    parser = argparse.ArgumentParser(description="Echo a message")

    parser.add_argument("message", nargs="*", help="Message to echo")
    parser.add_argument("--upper", action="store_true", help="Convert to uppercase")
    parser.add_argument("--prefix", default="", help="Prefix to add")

    parsed_args = parser.parse_args(args)

    message = " ".join(parsed_args.message) if parsed_args.message else "Hello, World!"

    if parsed_args.upper:
        message = message.upper()

    if parsed_args.prefix:
        message = f"{parsed_args.prefix}: {message}"

    print(message)


if __name__ == "__main__":
    main()
