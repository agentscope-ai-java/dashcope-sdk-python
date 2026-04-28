import json

from dashscope.finetune.reinforcement import (logger, FunctionType,
                                              AgenticRLTuning, AgenticRLFunctionComponent, FunctionComponentModel, FunctionComponentRuntime,
                                              RolloutInput, RewardInput, RewardOutput, RolloutOutput)
from dashscope.finetune.agentic_rl import AgenticRL
from dashscope.finetune.finetunes import FineTunes


async def main_functions():
    """Main execution workflow"""
    try:
        logger.info("Starting main tests workflow")
        client = AgenticRL()

        # Register functions
        (rollout_entity_ids,
         reward_entity_ids,
         group_reward_entity_ids,
         rollout_instance_ids,
         reward_instance_ids,
         group_reward_instance_ids) = \
            await client.register_functions(
                functions=[
                    AgenticRLFunctionComponent(
                        type=FunctionType.ROLLOUT,
                        fcmodel=FunctionComponentModel(
                            classpath="functions.rollout.demo_rollout2.DemoRolloutProcessor"),
                    ),

                    # AgenticRLFunctionComponent(
                    #     type=FunctionType.ROLLOUT,
                    #     fcmodel=FunctionComponentModel(
                    #         classpath="functions.rollout.demo_rollout.CalcXRolloutProcessor"),
                    # ),

                    # AgenticRLFunctionComponent(
                    #     type=FunctionType.REWARD,
                    #     fcmodel=FunctionComponentModel(
                    #         classpath="functions/reward/demo_reward_decorator.py:SafetyProcessor"),
                    # ),

                    AgenticRLFunctionComponent(
                        type=FunctionType.REWARD,
                        fcmodel=FunctionComponentModel(
                            classpath="functions.reward.demo_reward.DemoRewardProcessor"),
                    ),

                    # AgenticRLFunctionComponent(
                    #     type=FunctionType.GROUP_REWARD,
                    #     fcmodel=FunctionComponentModel(
                    #         classpath="functions.reward.demo_group_reward.DemoGroupRewardProcessor"),
                    # ),
                ],
                lazy_load=False) # register & load functions
        logger.info(f"agentic rl register functions: {rollout_entity_ids=}, {reward_entity_ids=}, {group_reward_entity_ids=}, {rollout_instance_ids=}, {reward_instance_ids=}, {group_reward_instance_ids=}")

        try:
            with open("./resources/rollout_input.json", "r") as file:
                json_data = json.load(file)
                rollout_input = json_data

            with open("./resources/reward_input.json", "r") as file:
                json_data = json.load(file)
                reward_input = json_data

            with open("./resources/reward_decorator_input.json", "r") as file:
                json_data = json.load(file)
                reward_decorator_input = json_data

            with open("./resources/group_reward_input.json", "r") as file:
                json_data = json.load(file)
                group_reward_input = json_data
        except FileNotFoundError:
            print("Error: File not found")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format")
        except Exception as e:
            print(f"Error: {str(e)}")

        # Testing rollout functions
        # rollout_instance_ids = ['ro-ins-59439417-efd5-468e-a19e-752c7d4bb9a5']
        if rollout_instance_ids:
            result = await AgenticRL.test_functions(instance_id=rollout_instance_ids[0],
                                                    type=FunctionType.ROLLOUT,
                                                    input_data=rollout_input)
            logger.info(f"agentic rl test rollout: {rollout_instance_ids[0]=}, {result=}")

        # if rollout_instance_ids:
        #     result = await AgenticRL.test_functions(instance_id=rollout_instance_ids[1],
        #                                             type=FunctionType.ROLLOUT,
        #                                             input_data=rollout_input)
        #     logger.info(f"agentic rl test rollout: {rollout_instance_ids[1]=}, {result=}")

        # Testing reward-decorator functions
        # reward_instance_ids = ['rw-ins-5cbb5f91-2a20-4b6c-88ba-1cc0ab434d75', 'rw-ins-76eb429b-70da-4c00-b79c-0925a2d7cce0']
        if reward_instance_ids and reward_instance_ids[0]:
            result = await AgenticRL.test_functions(instance_id=reward_instance_ids[0],
                                                    type=FunctionType.REWARD,
                                                    input_data=reward_decorator_input)
            reward_score = result.get('reward', {}).get('reward_score', 0.0)
            assert reward_score == 0.85, f"Expected reward_score 0.85, got {reward_score}"
            logger.info(f"agentic rl test rewards-decorator: {reward_instance_ids[0]=}, {result=}")

        # Testing reward functions
        # reward_instance_ids = ['rw-ins-5cbb5f91-2a20-4b6c-88ba-1cc0ab434d75', 'rw-ins-76eb429b-70da-4c00-b79c-0925a2d7cce0']
        # if reward_instance_ids and reward_instance_ids[1]:
        #     result = await AgenticRL.test_functions(instance_id=reward_instance_ids[1],
        #                                             type=FunctionType.REWARD,
        #                                             input_data=reward_input)
        #     logger.info(f"agentic rl test rewards: {reward_instance_ids[1]=}, {result=}")

        # Testing group-reward functions
        # group_reward_instance_ids = ['grw-ins-6858dc42-5f03-438b-8662-0bb33633a24d']
        # if group_reward_instance_ids and group_reward_instance_ids[0]:
        #     result = await AgenticRL.test_functions(instance_id=group_reward_instance_ids[0],
        #                                             type=FunctionType.GROUP_REWARD,
        #                                             input_data=group_reward_input)
        #     logger.info(f"agentic rl test group-rewards: {group_reward_instance_ids[0]=}, {result=}")

        logger.info("All tests workflows completed successfully")

    except Exception as e:
        logger.error(f"Main execution flow terminated: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main_functions())
