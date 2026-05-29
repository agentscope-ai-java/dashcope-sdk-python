# -*- coding: utf-8 -*-
"""Allow ``python -m dashscope.cli`` invocation."""
import warnings

# Suppress urllib3 NotOpenSSLWarning on systems with LibreSSL
warnings.filterwarnings(
    "ignore",
    message=".*urllib3.*only supports OpenSSL.*",
    category=Warning,
)

import sys
from dashscope.cli import main

main()
