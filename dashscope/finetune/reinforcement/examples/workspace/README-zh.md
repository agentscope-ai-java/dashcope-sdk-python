# Agentic RL SDK/CLI 使用指南 [[English]](./README.md)

## 1. 安装 SDK

```bash
pip install dashscope>=1.25.19
```

## 2. 环境配置

### 2.1 设置环境变量

```bash
# 必填：API密钥（也可在代码中初始化: AgenticRL(api_key="for your api key") ）
export DASHSCOPE_API_KEY="your_api_key_here"

# 可选：日志级别设置info/debug/warning/critical（默认info）
export LOG_LEVEL="info"
```

### 2.2 配置依赖文件

创建`requirements.txt`文件，包含以下核心依赖：

```requirements.txt
# 基础（必须）
dashscope>=1.25.19

# 框架依赖
fastapi==0.136.0
uvicorn==0.45.0
# 省略

# 轨迹函数依赖
langchain-core==1.3.0
langchain-mcp-adapters==0.2.2
langchain-openai==1.2.0
# 省略

# 添加其他自定义依赖...
```

## 3. 函数开发与数据准备

### 3.1 创建函数组件

在`functions`目录下开发函数：

- **奖励函数模板**：
    - `functions/reward/reward.py` - 基础实现
    - `functions/reward/reward_decorator.py` - 装饰器实现
- **轨迹函数模板**：
    - `functions/rollout/rollout.py` - 基础实现

> 注：functions/目录下需要包含__init__.py文件

### 3.2 准备训练数据

在`data`目录下添加数据集文件：

- `data/calc_training_min.jsonl` - 训练数据集（JSONL格式）
- `data/calc_validation_min.jsonl` - 验证数据集（JSONL格式）

## 4. 使用SDK执行任务

### 4.1 函数执行（注册+测试）

```bash
python test_functions.py
```

### 4.2 工作流执行（YAML配置+生命周期管理）

```bash
python submit_job.py
```

## 5. 使用CLI执行任务

```bash
dashscope rl --help  # 查看完整命令帮助
```

```bash
 Usage: dashscope [OPTIONS] COMMAND [ARGS]...

 🚀 Agentic RL Fine-Tuning CLI

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ register_functions  🧩 Register Rollout/Reward function components, returns entity_id & instance_id                                                                                                             │
│ test_functions      🧪 Test a registered Rollout/Reward function instance with custom input data.                                                                                                               │
│ upload_data         📦 Upload training/validation datasets to the platform, returns file IDs                                                                                                                    │
│ run                 🚀 Launch the complete RL tuning workflow (function registration → dataset upload → job submission)                                                                                         │
│ get                 📊 Query the current status and metadata of a specific job                                                                                                                                  │
│ list                📋 List historical fine-tuning jobs with pagination                                                                                                                                         │
│ cancel              🛑 Cancel a running job                                                                                                                                                                     │
│ delete              🗑️ Delete a job record (releases metadata)                                                                                                                                                  │
│ logs                📜 Fetch job execution logs (supports pagination)                                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

dashscope rl register_functions \
  --rollout-classpaths "functions.rollout.rollout_only.DemoRolloutProcessor" \
  --no-lazy-load \
  --output-format json

ROLLOUT_INSTANCE_ID="ro-ins-****"
dashscope rl test_functions "$ROLLOUT_INSTANCE_ID" \
  --type rollout \
  --input ./resources/rollout_input.json

dashscope rl run -c job.yaml -o json

JOB_ID="ft-****"
dashscope rl get "$JOB_ID" -o json
dashscope rl cancel "$JOB_ID"
```

## 最佳实践提示

1. **开发测试**：使用`test_functions`命令在提交前验证函数逻辑
2. **增量开发**：修改函数后重新注册即可，无需重建整个环境
3. **日志排查**：设置`LOG_LEVEL=debug`获取详细调试信息
4. **资源管理**：任务完成后使用`delete`命令释放资源

> 注：所有路径和参数需根据实际项目调整，示例脚本位于项目`workspace/`目录下
>
> 注：项目`workspace/`目录下的所有文件都会打包上传到远程进行在线计算，注意数据安全
>
> 注：项目`workspace/`目录下，设置上传排除的子目录和文件，参考环境变量：FC_ZIP_EXCLUDE_PATTERNS
>
> 注：项目`workspace/`目录下的所有文件打包上传限制大小：200M；可以通过环境变量FC_OSS_FILE_SIZE_WARNING修改
>
> 注：如果要使用本地build的dashscope whl包（通过scripts/build.sh脚本生成），可以设置：
> export FC_PYPI_LIB="dashscope-1.25.19-py3-none-any.whl"，
> 并且放置在项目目录下workspace/；再把requirements.txt中dashscope依赖去掉。
