import json

from dashscope.finetune.reinforcement import (logger,
                                              AgenticRLTuning, AgenticRLFunctionComponent, FunctionComponentModel, FunctionComponentRuntime, FunctionType,
                                              RolloutInput, RewardInput, RewardOutput, RolloutOutput)
from dashscope.finetune.agentic_rl import AgenticRL
from dashscope.finetune.finetunes import FineTunes


async def main_workflow_yaml():
    #### 1️⃣ Configuration-Driven (Recommended)
    client = AgenticRL()
    client.init(
        config_path="config.yaml",
        job_name="test-0428-3",
    )
    result = await client.run(
        lazy_load=False)  # Automatically reads cached configuration, no arguments required
    if result.status_code == 200:
        job_id = result.output.job_id
        logger.info(f"agentic rl(from config.yaml) submit: {job_id=}, {result=}")
    else:
        raise ValueError(f"agentic rl(from config.yaml) submit: {result}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main_workflow_yaml())
