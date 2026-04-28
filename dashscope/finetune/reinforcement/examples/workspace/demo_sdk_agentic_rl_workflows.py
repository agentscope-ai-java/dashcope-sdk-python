import json

from dashscope.finetune.reinforcement import (logger,
                                              AgenticRLTuning, RolloutFunctionComponent, RewardFunctionComponent, FunctionComponentModel, FunctionComponentRuntime,
                                              RolloutInput, RewardInput, RewardOutput, RolloutOutput,
                                              AgenticRLFunctionComponent, FunctionType)
from dashscope.finetune.agentic_rl import AgenticRL
from dashscope.finetune.finetunes import FineTunes


async def main_workflow():
    """Main execution workflow"""
    try:
        logger.info("Starting main tests workflow")

        rollout_runtime = {"cpu": 2, "memory_size": 4096, "disk_size": 512, "concurrency": 30,
                           "env": {}, "capacity": 30, "min_capacity": 30, "max_capacity": 60,
                           "memory_scale_threshold": 0.6,"concurrency_scale_threshold": 0.6}

        reward_runtime = FunctionComponentRuntime(
            cpu=2,
            memory_size=4096,
            disk_size=512,
            concurrency=30,
            env={},
            capacity=30,
            min_capacity=30,
            max_capacity=60,
            memory_scale_threshold=0.6,
            concurrency_scale_threshold=0.6,
        )

        client = AgenticRL()
        result = await client.run(
            model="qwen3-4b-instruct-2507",
            training_files=["./data/calc_train.jsonl"],
            validation_files=["./data/calc_validation.jsonl"],
            functions=[
                RolloutFunctionComponent(
                    name="rollout-1",
                    fcmodel=FunctionComponentModel(
                        classpath="functions.rollout.demo_rollout.CalcXRolloutProcessor"),
                    runtime = FunctionComponentRuntime(**rollout_runtime)),

                RewardFunctionComponent(
                    name="reward-1",
                    weight=1.0,
                    reward_metric_weight={"reward_metric_weightA": 0.3, "reward_metric_weightB": 0.7},
                    fcmodel=FunctionComponentModel(
                        classpath="functions.reward.demo_reward.DemoRewardProcessor"),
                    runtime=reward_runtime),

                # RewardFunctionComponent(
                #     weight=1.0,
                #     fcmodel=FunctionComponentModel(
                #         classpath="functions/reward/demo_reward_decorator.py:SafetyProcessor"),
                #     runtime=reward_runtime),

                # AgenticRLFunctionComponent(
                #     type=FunctionType.GROUP_REWARD,
                #     name="group-reward-1",
                #     weight=1.2,
                #     fcmodel=FunctionComponentModel(
                #         classpath="functions.reward.demo_group_reward.DemoGroupRewardProcessor"),
                #     runtime=reward_runtime),
            ],
            job_name='test-0428',
            hyper_parameters={
                "n_epochs": 1,
                "learning_rate": 1e-6,
                "max_prompt_length": 2048,
                "batch_size": 128
            })

        if result.status_code == 200:
            job_id = result.output.job_id
            logger.info(f"agentic rl submit: {job_id=}, {result=}")
        else:
            raise ValueError(f"agentic rl submit: {result}")

        # Get rl job
        result = AgenticRL.get(job_id=job_id)
        status = result.output.status
        logger.info(f"agentic rl get: {job_id=}, {status=}, {result=}")

        # Cancel rl job
        # result = AgenticRL.cancel(job_id=job_id)
        # logger.info(f"agentic rl cancel: {job_id=}, {result=}")

        logger.info("All tests workflows completed successfully")

    except Exception as e:
        logger.error(f"Main execution flow terminated: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main_workflow())
