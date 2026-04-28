import json

from dashscope.finetune.reinforcement import (logger, FunctionType,
                                              AgenticRLTuning, AgenticRLFunctionComponent, FunctionComponentRuntime,
                                              RolloutInput, RewardInput, RewardOutput, RolloutOutput)
from dashscope.finetune.agentic_rl import AgenticRL
from dashscope.finetune.finetunes import FineTunes


async def main_tuning():
    """Main execution workflow"""
    try:
        logger.info("Starting main tests workflow")

        client = AgenticRL()

        # training_file_ids, validation_file_ids = await client.upload_datasets(
        #     training_files=["./data/training.jsonl"],
        #     validation_files=["./data/validation.jsonl"]
        # )
        training_file_ids = "13822545-4da6-4e62-809a-1e7b26d1b491",

        rollout_id = 'ro-815680c1-4f59-42a6-99bd-eea1c66a3413'
        reward_ids = ['rw-87132f06-24c6-497b-a8c1-6f5711cfda31', 'rw-ff2671bf-fc81-4467-a248-ad34aa206766']
        group_reward_ids = ['grw-ae4e8fbb-2107-4fe8-a64c-8701838852f4']
        rollout_runtime = {"cpu": 2, "memory_size": 4096, "disk_size": 10240, "concurrency": 2,
                           "env": {}, "capacity": 5}
        reward_runtimes = [
            {"cpu": 2, "memory_size": 4096, "disk_size": 512, "concurrency": 30, "env": {},
             "capacity": 30, "min_capacity": 30, "max_capacity": 60, "memory_scale_threshold": 0.6, "concurrency_scale_threshold": 0.6},
            {"cpu": 2, "memory_size": 4096, "disk_size": 10240, "concurrency": 5, "env": {},
             "capacity": 6}]
        group_reward_runtimes = [
            {"cpu": 2, "memory_size": 4096, "disk_size": 10240, "concurrency": 10, "env": {},
             "capacity": 8}]
        hyper_parameters = {
            "n_epochs": 1,
            "learning_rate": 1e-4,
            "max_prompt_length": 2048,
            "batch_size": 128
        }

        functions = [
            AgenticRLFunctionComponent(
                type=FunctionType.ROLLOUT,
                #name="rollout-1",
                entity_id=rollout_id,
                runtime=FunctionComponentRuntime(**rollout_runtime)),
            AgenticRLFunctionComponent(
                type=FunctionType.REWARD,
                name="reward-1",
                weight=1.0,
                reward_metric_weight={"reward_metric_weightA": 0.3, "reward_metric_weightB": 0.7},
                entity_id=reward_ids[0],
                runtime=FunctionComponentRuntime(**reward_runtimes[0])),
            AgenticRLFunctionComponent(
                type=FunctionType.REWARD,
                name="reward-2",
                weight=1.0,
                entity_id=reward_ids[1],
                runtime=FunctionComponentRuntime(**reward_runtimes[1])),
            # AgenticRLFunctionComponent(
            #     type=FunctionType.GROUP_REWARD,
            #     weight=1.0,
            #     entity_id=group_reward_ids[0],
            #     runtime=FunctionComponentRuntime(**group_reward_runtimes[0])),
        ]

        result = client.submit_job(
            model="qwen3-4b-instruct-2507",
            training_file_ids=training_file_ids,
            functions=functions,
            hyper_parameters=hyper_parameters)
        if result.status_code == 200:
            job_id = result.output.job_id
            logger.info(f"agentic rl submit: {job_id=}, {result=}")
        else:
            raise ValueError(f"agentic rl submit: {result}")

        # Get rl job
        result = AgenticRL.get(job_id=job_id)
        status=result.output.status
        logger.info(f"agentic rl get: {job_id=}, {status=}, {result=}")

        # Cancel rl job
        # result = AgenticRL.cancel(job_id=job_id)
        # logger.info(f"agentic rl cancel: {job_id=}, {result=}")

        # List Jobs
        # logs = AgenticRL.list(page_no=1, page_size=10)

        logger.info("All tests workflows completed successfully")

    except Exception as e:
        logger.error(f"Main execution flow terminated: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main_tuning())
