# Agent Instructions

## Response Style
- Be concise in responses - avoid over-explaining changes
- Focus on the specific task requested rather than extensive commentary

## Development Workflow
- Document design decisions in code for future reference
- Always run unit tests after making changes using `uv run pytest`

## Diagnostic Handling
For diagnostic warnings, use specific Pyright ignore comments with error codes:
- `# pyright: ignore[reportAny]` for "Type is Any" warnings
- `# pyright: ignore[reportImplicitOverride]` for unittest method override warnings
- Use `_ = function_call()` assignment for unused return value warnings