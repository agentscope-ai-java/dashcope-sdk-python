# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
"""Allow ``python -m dashscope.cli`` invocation."""
import warnings

# Suppress urllib3 NotOpenSSLWarning on systems with LibreSSL
warnings.filterwarnings(
    "ignore",
    message=".*urllib3.*only supports OpenSSL.*",
    category=Warning,
)

# fmt: off
from dashscope.cli import main  # noqa: E402
# fmt: on

main()
