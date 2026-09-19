# 개발 가이드

> [English](develop.md) | [中文](develop_zh.md) | [日本語](develop_ja.md) | [Español](develop_es.md) | **한국어**

## 1. 코드 스타일

코드 스타일은 [PEP8](https://www.python.org/dev/peps/pep-0008/)을 기본으로 채택합니다.

린팅과 포맷팅에는 다음 도구를 사용합니다:
- [flake8](http://flake8.pycqa.org/en/latest/): 린터
- [yapf](https://github.com/google/yapf): 포맷터
- [isort](https://github.com/timothycrosley/isort): import 정렬

yapf와 isort의 스타일 설정은 [setup.cfg](../../setup.cfg)에서 확인할 수 있습니다.
[pre-commit hook](https://pre-commit.com/)을 사용하여 커밋할 때마다 `flake8`, `yapf`, `seed-isort-config`, `isort`, `trailing whitespaces`를 자동으로 검사하고 포맷팅하며,
`end-of-files`를 수정하고 `requirements.txt`를 자동으로 정렬합니다.
pre-commit hook 설정은 [.pre-commit-config](../../.pre-commit-config.yaml)에 저장되어 있습니다.
저장소를 클론한 후에는 pre-commit hook을 설치하고 초기화해야 합니다.
```bash
pip install -r requirements-test.txt
```
저장소 루트 디렉터리에서:
```bash
pre-commit install
```

이후에는 커밋할 때마다 코드 린팅과 포맷팅이 자동으로 적용됩니다.

모든 파일에 대해 pre-commit 검사를 실행하고 싶다면 다음을 실행하세요:
```bash
pre-commit run --all-files
```

코드 포맷팅과 검사만 실행하고 싶다면 다음을 실행하세요:
```bash
make linter
```
