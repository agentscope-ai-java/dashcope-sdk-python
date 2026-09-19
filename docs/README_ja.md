> [English](README.md) | [中文](README_zh.md) | **日本語** | [Español](README_es.md) | [한국어](README_ko.md)

## ドキュメントのメンテナンス

1. ドキュメントのビルド
    ```shell
    # リポジトリのルートディレクトリで：
    make docs
    ```

2. docstring のフォーマット

    標準として Google スタイルの docstring フォーマットを採用しています。詳細は以下のドキュメントを参照してください。
    1. Google Python style guide docstring [リンク](http://google.github.io/styleguide/pyguide.html#381-docstrings)
    2. Google docstring の例 [リンク](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
    3. サンプル：torch.nn.modules.conv [リンク](https://pytorch.org/docs/stable/_modules/torch/nn/modules/conv.html#Conv1d)
    4. load 関数を例にすると：

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
