"""
component/demo/reward_processor_demo.py

Demo implementation of Reward Processor.
Demonstrates rule-based scoring for Agent outputs.
"""

from dashscope.finetune.reinforcement.common.log import logger
from dashscope.finetune.reinforcement.component.data.base_data_model import (
    TaskStatus,
)
from dashscope.finetune.reinforcement.component.data.reward_input import (
    RewardInput,
)
from dashscope.finetune.reinforcement.component.data.reward_output import (
    RewardOutput,
    Reward,
)
from dashscope.finetune.reinforcement.component.processor.abstract_reward_processor import (
    AbstractRewardProcessor,
)


class DemoRewardProcessor(AbstractRewardProcessor):
    """
    Demo implementation of Reward Processor.
    Demonstrates rule-based scoring for Agent outputs.

    Scoring Strategy:
    - Reward 1.0 if ground_truth exists and is contained in agent_output messages
    - Reward 0.5 if agent_output has messages
    - Default reward 0.0 otherwise
    """

    def setup(self) -> None:
        """
        Initialize workspace before processing requests.

        Demo implementation: Logs startup message.
        In production, this could load embedding models, initialize databases, etc.
        """
        logger.info(
            "[DemoRewardProcessor] setup() called - initializing workspace"
        )
        # Demo: No actual initialization needed
        # In production, you might:
        # - Load embedding models for semantic similarity
        # - Initialize database connections for storing rewards
        # - Load configuration files
        logger.info("[DemoRewardProcessor] setup() completed")

    def process(self, rl_input: RewardInput) -> RewardOutput:
        """
        Demo implementation: Calculate simple rewards based on agent_output messages
        and ground_truth matching.

        Args:
            rl_input: RewardInput input parameter

        Returns:
            RewardOutput object containing standardized reward calculation
        """
        logger.info(
            f"[DemoRewardProcessor] computing reward for rollout_id={rl_input.rollout_id}"
        )

        score = 0.0

        if rl_input.ground_truth is not None and rl_input.agent_output.message:
            gt_str = str(rl_input.ground_truth)
            for msg in rl_input.agent_output.message:
                if (
                    isinstance(msg.get("content"), str)
                    and gt_str in msg["content"]
                ):
                    score = 1.0
                    break
            if score == 0.0 and len(rl_input.agent_output.message) > 0:
                score = 0.5

        result = RewardOutput(
            reward=Reward(
                reward_score=score,
                reward_metrics=rl_input.agent_output.rollout_metrics,
            ),
            status=TaskStatus.SUCCESS,
            error=None,
        )
        logger.info(f"[DemoRewardProcessor] result: {result}")
        return result
