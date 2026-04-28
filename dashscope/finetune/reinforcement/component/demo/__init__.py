from dashscope.finetune.reinforcement.component.demo.reward_processor_demo import DemoRewardProcessor
from dashscope.finetune.reinforcement.component.demo.rollout_processor_demo import DemoRolloutProcessor
from dashscope.finetune.reinforcement.component.demo.group_reward_processor_demo import DemoGroupRewardProcessor

__all__ = [
    "DemoRewardProcessor",  # Inherits AbstractRewardProcessor, returns RewardOutput
    "DemoRolloutProcessor",  # Inherits AbstractRolloutProcessor, returns RolloutOutput
    "DemoGroupRewardProcessor",  # Inherits AbstractGroupRewardProcessor, returns GroupRewardOutput
]