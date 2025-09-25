# Design Decisions

## Core Philosophy
- **Dependency-free**: Uses only Python3 standard library (os, sys, datetime, argparse, unittest)
- **Single file**: Contains both main functionality and unit tests for easy deployment
- **Functional approach**: Avoids OOP, uses simple functions for clarity and maintainability

## State Management
- **State tracking**: Uses ~/.start_the_day.toml to track execution state and prevent multiple runs per day
- **Cross-day detection**: Uses date comparison rather than 24-hour intervals for "daily" logic
- **TOML format**: Human-readable config format, implemented with simple parsing/writing

## Error Handling & Reliability
- **Error handling**: Graceful handling of file I/O errors and malformed config
- **Exit codes**: 0 for success/already ran, 1 for errors, 2 for test failures
- **Logging**: Simple print statements for user feedback, no external logging dependencies

## Testing Strategy
- **Test integration**: --test flag runs embedded unit tests using Python's unittest framework
- **Testing approach**: Integration-style tests using separate config file (~/.start_the_day_test.toml) rather than complex mocking - more reliable, easier to debug, and tests real file I/O behavior

## Code Quality
- **Type safety**: Comprehensive type annotations for better IDE support and static analysis, with acceptable remaining diagnostics for argparse/unittest patterns that are inherently dynamic