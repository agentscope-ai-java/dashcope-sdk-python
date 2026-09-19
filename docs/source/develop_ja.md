# 開発ガイド

> [English](develop.md) | [中文](develop_zh.md) | **日本語** | [Español](develop_es.md) | [한국어](develop_ko.md)

## 1. コードスタイル

コードスタイルには [PEP8](https://www.python.org/dev/peps/pep-0008/) を採用しています。

リンティングとフォーマットには以下のツールを使用しています：
- [flake8](http://flake8.pycqa.org/en/latest/)：リンター
- [yapf](https://github.com/google/yapf)：フォーマッター
- [isort](https://github.com/timothycrosley/isort)：import の並び替え

yapf と isort のスタイル設定は [setup.cfg](../../setup.cfg) にあります。
[pre-commit hook](https://pre-commit.com/) を使用しており、コミットのたびに `flake8`、`yapf`、`seed-isort-config`、`isort`、`trailing whitespaces` のチェックとフォーマットを自動的に行い、
`end-of-files` を修正し、`requirements.txt` を自動的に整理します。
pre-commit hook の設定は [.pre-commit-config](../../.pre-commit-config.yaml) に保存されています。
リポジトリをクローンしたら、pre-commit hook をインストールして初期化する必要があります。
```bash
pip install -r requirements-test.txt
```
リポジトリのルートディレクトリで：
```bash
pre-commit install
```

これ以降、コミットのたびにコードのリンティングとフォーマットが自動的に適用されます。

すべてのファイルに対して pre-commit チェックを実行したい場合は、次のコマンドを実行してください：
```bash
pre-commit run --all-files
```

コードのフォーマットとチェックだけを行いたい場合は、次のコマンドを実行してください：
```bash
make linter
```
