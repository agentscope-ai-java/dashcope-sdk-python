# Desarrollo

> [English](develop.md) | [中文](develop_zh.md) | [日本語](develop_ja.md) | **Español** | [한국어](develop_ko.md)

## 1. Estilo de código

Adoptamos [PEP8](https://www.python.org/dev/peps/pep-0008/) como el estilo de código preferido.

Usamos las siguientes herramientas para el linting y el formateo:
- [flake8](http://flake8.pycqa.org/en/latest/): linter
- [yapf](https://github.com/google/yapf): formateador
- [isort](https://github.com/timothycrosley/isort): ordena los imports

Las configuraciones de estilo de yapf e isort se encuentran en [setup.cfg](../../setup.cfg).
Usamos un [pre-commit hook](https://pre-commit.com/) que verifica y formatea `flake8`, `yapf`, `seed-isort-config`, `isort`, `trailing whitespaces`,
corrige `end-of-files` y ordena automáticamente `requirements.txt` en cada commit.
La configuración del pre-commit hook se guarda en [.pre-commit-config](../../.pre-commit-config.yaml).
Después de clonar el repositorio, deberás instalar e inicializar el pre-commit hook.
```bash
pip install -r requirements-test.txt
```
Desde la carpeta del repositorio:
```bash
pre-commit install
```

A partir de aquí, en cada commit se aplicarán automáticamente el linting y el formateo del código.

Si quieres ejecutar la verificación de pre-commit en todos los archivos, puedes ejecutar:
```bash
pre-commit run --all-files
```

Si solo quieres formatear y verificar tu código, puedes ejecutar:
```bash
make linter
```
