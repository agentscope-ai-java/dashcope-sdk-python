# -*- coding: utf-8 -*-
"""Allow ``python -m dashscope.cli`` invocation."""
import sys

from dashscope.cli import main

sys.exit(main() or 0)
