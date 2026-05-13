"""
component/demo/group_reward_processor_demo.py

Demo implementation of GroupReward Processor.
Demonstrates rule-based scoring for multiple Agent outputs in a group.
"""

from dashscope.finetune.reinforcement.common.log import logger
from dashscope.finetune.reinforcement.component.data.base_data_model import (
    TaskStatus,
)
from dashscope.finetune.reinforcement.component.data.group_reward_input import (
    GroupRewardInput,
)
from dashscope.finetune.reinforcement.component.data.group_reward_output import (
    GroupRewardOutput,
)
from dashscope.finetune.reinforcement.component.data.group_reward_output import (
    GroupRewardOutput,
    GroupReward,
)
from dashscope.finetune.reinforcement.component.data.reward_output import (
    Reward,
)
from dashscope.finetune.reinforcement.component.processor.abstract_group_reward_processor import (
    AbstractGroupRewardProcessor,
)


class DemoGroupRewardProcessor(AbstractGroupRewardProcessor):
    """
    Demo implementation of GroupReward Processor.
    Demonstrates rule-based scoring for multiple Agent outputs in a group.

    Scoring Strategy:
    - For each agent_output, check if ground_truth exists and is contained in messages
    - Reward 1.0 if ground_truth is found in messages
    - Reward 0.5 if messages length > 0
    - Default reward 0.0 otherwise
    """

    def setup(self) -> None:
        """
        Initialize workspace before processing requests.

        Demo implementation: Logs startup message.
        In production, this could load embedding models, initialize databases, etc.
        """
        logger.info(
            "[DemoGroupRewardProcessor] setup() called - initializing workspace"
        )
        # Demo: No actual initialization needed
        # In production, you might:
        # - Load embedding models for semantic similarity
        # - Initialize database connections for storing rewards
        # - Load configuration files
        logger.info("[DemoGroupRewardProcessor] setup() completed")

    def process(self, input: GroupRewardInput) -> GroupRewardOutput:
        """
        Demo implementation: Calculate simple rewards for multiple agent outputs
        based on ground_truth matching.

        Args:
            input: GroupRewardInput input parameter

        Returns:
            GroupRewardOutput object containing standardized group reward calculation
        """
        logger.info(
            f"[DemoGroupRewardProcessor] computing group reward for {len(input.agent_outputs)} outputs"
        )

        rewards = []
        for idx, agent_output in enumerate(input.agent_outputs):
            score = 0.0

            # Check if ground_truth is in messages
            if input.ground_truth is not None and agent_output.message:
                gt_str = str(input.ground_truth)
                for msg in agent_output.message:
                    if (
                        isinstance(msg.get("content"), str)
                        and gt_str in msg["content"]
                    ):
                        score = 1.0
                        break
                if score == 0.0 and len(agent_output.message) > 0:
                    score = 0.5

            rewards.append(
                Reward(
                    reward_score=score,
                    reward_metrics=agent_output.rollout_metrics,
                )
            )
            logger.info(
                f"[DemoGroupRewardProcessor] output {idx}: score={score}"
            )

        result = GroupRewardOutput(
            reward=GroupReward(rewards=rewards),
            status=TaskStatus.SUCCESS,
            error=None,
        )
        logger.info(
            f"[DemoGroupRewardProcessor] result: rewards_count={len(rewards)}"
        )
        return result
