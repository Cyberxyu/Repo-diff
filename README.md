# repo-diff

项目简介
- repo-diff 是一个命令行工具，用于对比两个 Git 仓库（或普通目录）在指定分支上的差异，并生成一份精美的 HTML 差异报告。
- 执行过程中会自动为 base 仓库添加临时 remote `comp` 并在完成后自动清理，保持仓库整洁。

先决条件
- Python 3.8 及以上
- Git（需要添加到系统 PATH）
- 安装依赖：

```
pip install -r requirements.txt
```

快速开始
- 使用示例：

```
python main.py <repo_base> <repo_comp> [branch_base] [branch_comp]
# 例如：
python main.py ./repo1 ./repo2
python main.py ./repo1 ./repo2 develop feature/new
```

- 参数说明：
  - `repo_base`：基准仓库路径
  - `repo_comp`：对比仓库路径
  - `branch_base`：基准分支（默认 master / main）
  - `branch_comp`：对比分支（默认 master / main）

- 输出：
  - 成功执行后，报告将生成到当前目录下的 `output/` 文件夹中
  - 文件名格式：`YYYY-MM-DD-<basename>-<compname>-diffreport.html`

打包为 exe
- 安装打包依赖：

```
pip install pyinstaller
```

- 运行打包脚本：

```
python build.py
```

- 打包完成后，可执行文件位于 `dist/repo-diff.exe`
- 使用方式与脚本一致：

```
repo-diff.exe ./repo1 ./repo2
```

项目结构（主要文件）
- [main.py](main.py)：程序入口，支持脚本与 PyInstaller 单文件模式
- [src/html_generator.py](src/html_generator.py)：HTML 差异报告生成器
- [src/repo-diff.py](src/repo-diff.py)：差异处理逻辑与 Git 交互
- [build.py](build.py)：PyInstaller 打包脚本
- [font/](font/)：报告字体资源
- [docs/](docs/)：文档与计划

贡献
- 欢迎提交 issue 或 pull request。如需贡献，请在 PR 描述中说明目标与复现步骤。

许可证
- 请根据需要在仓库根目录添加 LICENSE 文件。
