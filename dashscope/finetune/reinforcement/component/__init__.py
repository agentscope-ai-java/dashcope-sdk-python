# ---------------------------------------------------------------------------- #
#                               Base Components                                #
# ---------------------------------------------------------------------------- #
from dashscope.finetune.reinforcement.component.data.base_data_model import (
    BaseDataModel,
    TaskStatus,
    ModelProtocol,
    Task,
    Resource,
    AgentOutput,
)
from dashscope.finetune.reinforcement.component.parser.base_parser import BaseRequestParser

# ---------------------------------------------------------------------------- #
#                              Func Manager                                    #
# ---------------------------------------------------------------------------- #
from dashscope.finetune.reinforcement.component.func_manager import (
    FuncManager,
)
from dashscope.finetune.reinforcement.component.func_decorator import (
    reward_func, sub_reward_func, aggregate_func
)

# ---------------------------------------------------------------------------- #
#                                 Data Models                                  #
# ---------------------------------------------------------------------------- #
from dashscope.finetune.reinforcement.component.data.reward_input import RewardInput
from dashscope.finetune.reinforcement.component.data.rollout_input import RolloutInput
from dashscope.finetune.reinforcement.component.data.reward_output import Reward, RewardOutput
from dashscope.finetune.reinforcement.component.data.rollout_output import RolloutOutput

# ---------------------------------------------------------------------------- #
#                                  Parsers                                     #
# ---------------------------------------------------------------------------- #
from dashscope.finetune.reinforcement.component.parser.reward_parser import RewardRequestParser
from dashscope.finetune.reinforcement.component.parser.rollout_parser import RolloutRequestParser

# ---------------------------------------------------------------------------- #
#                                Processors                                    #
# ---------------------------------------------------------------------------- #
from dashscope.finetune.reinforcement.component.processor.abstract_reward_processor import AbstractRewardProcessor
from dashscope.finetune.reinforcement.component.processor.abstract_rollout_processor import AbstractRolloutProcessor

# ---------------------------------------------------------------------------- #
#                                   Demos                                      #
# ---------------------------------------------------------------------------- #
from dashscope.finetune.reinforcement.component.demo.reward_processor_demo import DemoRewardProcessor
from dashscope.finetune.reinforcement.component.demo.rollout_processor_demo import DemoRolloutProcessor

# ---------------------------------------------------------------------------- #
#                                   Observability                              #
# ---------------------------------------------------------------------------- #
from dashscope.finetune.reinforcement.component.observability import observe_processor

__all__ = [
    # Base
    "BaseRequestParser",
    "BaseProcessor",
    "BaseDataModel",
    "TaskStatus",
    "ModelProtocol",
    "Task",
    "Resource",
    "AgentOutput",
    # Func Manager
    "FuncManager",
    "reward_func",
    "sub_reward_func",
    "aggregate_func",
    # Data Models
    "RewardInput",
    "RolloutInput",
    "Reward",
    "RewardOutput",
    "RolloutOutput",
    # Parsers
    "RewardRequestParser",
    "RolloutRequestParser",
    # Processors
    "AbstractRewardProcessor",
    "AbstractRolloutProcessor",
    # Demos
    "DemoRewardProcessor",
    "DemoRolloutProcessor",
    # Observability
    "observe_processor",
]
