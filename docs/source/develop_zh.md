# 开发指南

> [English](develop.md) | **中文** | [日本語](develop_ja.md) | [Español](develop_es.md) | [한국어](develop_ko.md)

## 1. 代码风格

我们采用 [PEP8](https://www.python.org/dev/peps/pep-0008/) 作为首选代码风格。

我们使用以下工具进行代码检查和格式化：
- [flake8](http://flake8.pycqa.org/en/latest/)：代码检查（linter）
- [yapf](https://github.com/google/yapf)：格式化工具
- [isort](https://github.com/timothycrosley/isort)：整理 import 顺序

yapf 和 isort 的样式配置可以在 [setup.cfg](../../setup.cfg) 中找到。
我们使用 [pre-commit hook](https://pre-commit.com/)，在每次提交时自动检查并格式化 `flake8`、`yapf`、`seed-isort-config`、`isort`、`trailing whitespaces`，
修复 `end-of-files`，并自动整理 `requirements.txt`。
pre-commit hook 的配置存放在 [.pre-commit-config](../../.pre-commit-config.yaml) 中。
克隆仓库后，你需要安装并初始化 pre-commit hook。
```bash
pip install -r requirements-test.txt
```
在仓库根目录下执行：
```bash
pre-commit install
```

完成以上步骤后，每次提交都会自动执行代码检查和格式化。

如果你想对所有文件运行 pre-commit 检查，可以执行：
```bash
pre-commit run --all-files
```

如果你只想格式化和检查代码，可以执行：
```bash
make linter
```
