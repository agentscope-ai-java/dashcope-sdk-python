# -*- coding: utf-8 -*-
"""Allow ``python -m dashscope.cli`` invocation."""
import sys


def _translate_legacy_args(argv):
    """Translate legacy argparse command format to Typer format.

    Legacy format:  dashscope fine_tunes.call --training_file_ids ...
    New format:     dashscope fine-tunes call --training-file-ids ...

    Returns modified argv list.
    """
    if len(argv) < 2:
        return argv

    # Command name mapping: old -> new
    command_map = {
        "fine_tunes.call": "fine-tunes call",
        "fine_tunes.get": "fine-tunes get",
        "fine_tunes.list": "fine-tunes list",
        "fine_tunes.stream": "fine-tunes stream",
        "fine_tunes.cancel": "fine-tunes cancel",
        "fine_tunes.delete": "fine-tunes delete",
        "generation.call": "generation call",
        "files.upload": "files upload",
        "files.get": "files get",
        "files.list": "files list",
        "files.delete": "files delete",
        "deployments.call": "deployments call",
        "deployments.get": "deployments get",
        "deployments.list": "deployments list",
        "deployments.scale": "deployments scale",
        "deployments.delete": "deployments delete",
        "oss.upload": "oss upload",
    }

    # Parameter name mapping: old -> new (underscore to dash)
    param_map = {
        "--training_file_ids": "--training-file-ids",
        "--validation_file_ids": "--validation-file-ids",
        "--n_epochs": "--n-epochs",
        "--batch_size": "--batch-size",
        "--learning_rate": "--learning-rate",
        "--prompt_loss": "--prompt-loss",
        "--hyper_parameters": "--hyper-parameters",
        "--file_id": "--file-id",
        "--deployed_model": "--deployed-model",
        "--base_url": "--base-url",
        "--api_key": "--api-key",
        "--start_page": "--start-page",
        "--page_size": "--page-size",
    }

    new_argv = [argv[0]]  # Keep program name
    i = 1

    # Check if first arg is a legacy command
    if i < len(argv) and argv[i] in command_map:
        # Split "fine_tunes.call" into ["fine-tunes", "call"]
        new_cmd = command_map[argv[i]].split()
        new_argv.extend(new_cmd)
        i += 1

    # Process remaining args
    while i < len(argv):
        arg = argv[i]

        # Translate parameter names
        if arg in param_map:
            new_argv.append(param_map[arg])
        else:
            new_argv.append(arg)

        i += 1

    return new_argv


def _extract_global_api_key(argv):
    """Extract global -k/--api-key from argv and set dashscope.api_key.

    Returns modified argv with api-key args removed.
    """
    import dashscope

    new_argv = []
    i = 0
    while i < len(argv):
        arg = argv[i]

        # Check for -k or --api-key
        if arg in ("-k", "--api-key"):
            # Next arg should be the key value
            if i + 1 < len(argv):
                dashscope.api_key = argv[i + 1]
                i += 2  # Skip both -k and the value
                continue
        elif arg.startswith("--api-key="):
            # Handle --api-key=value format
            dashscope.api_key = arg.split("=", 1)[1]
            i += 1
            continue

        new_argv.append(arg)
        i += 1

    return new_argv


if __name__ == "__main__":
    _argv = _extract_global_api_key(sys.argv)
    _argv = _translate_legacy_args(_argv)
    sys.argv = _argv

    from dashscope.cli import main

    main()
