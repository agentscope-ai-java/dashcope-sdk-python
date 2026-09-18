> [English](README.md) | **中文** | [日本語](README_ja.md)

## 维护文档

1. 构建文档
    ```shell
    # 在仓库根目录下执行：
    make docs
    ```

2. 文档字符串（docstring）格式

    我们采用 Google 风格的 docstring 格式作为标准，请参考以下文档。
    1. Google Python 风格指南 docstring [链接](http://google.github.io/styleguide/pyguide.html#381-docstrings)
    2. Google docstring 示例 [链接](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
    3. 示例：torch.nn.modules.conv [链接](https://pytorch.org/docs/stable/_modules/torch/nn/modules/conv.html#Conv1d)
    4. 以 load 函数为例：

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
