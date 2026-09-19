> [English](README.md) | [中文](README_zh.md) | [日本語](README_ja.md) | **Español** | [한국어](README_ko.md)

## Mantenimiento de la documentación

1. Compilar la documentación
    ```shell
    # en el directorio raíz del repositorio:
    make docs
    ```

2. Formato de las docstrings

    Adoptamos el formato de docstring estilo Google como estándar; consulta los siguientes documentos.
    1. Guía de estilo de Google para docstrings en Python [enlace](http://google.github.io/styleguide/pyguide.html#381-docstrings)
    2. Ejemplo de docstring de Google [enlace](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
    3. Ejemplo: torch.nn.modules.conv [enlace](https://pytorch.org/docs/stable/_modules/torch/nn/modules/conv.html#Conv1d)
    4. Tomando la función load como ejemplo:

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
