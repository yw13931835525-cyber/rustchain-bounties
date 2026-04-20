"""Allow: python -m rustchain_mcp"""
from .server import main
import asyncio
asyncio.run(main())
