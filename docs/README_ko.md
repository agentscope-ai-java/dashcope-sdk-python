> [English](README.md) | [中文](README_zh.md) | [日本語](README_ja.md) | [Español](README_es.md) | **한국어**

## 문서 유지보수

1. 문서 빌드
    ```shell
    # 저장소 루트 디렉터리에서:
    make docs
    ```

2. docstring 형식

    표준으로 Google 스타일의 docstring 형식을 채택합니다. 자세한 내용은 다음 문서를 참고하세요.
    1. Google Python 스타일 가이드 docstring [링크](http://google.github.io/styleguide/pyguide.html#381-docstrings)
    2. Google docstring 예시 [링크](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
    3. 예시: torch.nn.modules.conv [링크](https://pytorch.org/docs/stable/_modules/torch/nn/modules/conv.html#Conv1d)
    4. load 함수를 예로 들면:

    ```python
    def load(file, file_format=None, **kwargs):
        """Load data from json/yaml/pickle files.

        This method provides a unified api for loading data from serialized files.

        Args:
            file (str or :obj:`Path` or file-like object): Filename or a file-like
                object.
            file_format (str, optional): If not specified, the file format will be
                inferred from the file extension, otherwise use the specified one.
                Currently supported formats include "json", "yaml/yml".

        Examples:
            >>> load('/path/of/your/file')  # file is stored in disk
            >>> load('https://path/of/your/file')  # file is stored on internet
            >>> load('oss://path/of/your/file')  # file is stored in petrel

        Returns:
            The content from the file.
        """
    ```
