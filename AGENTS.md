# AGENTS.md - 技能翻译与审核项目
本文件包含代码库的操作规范和风格指南，供所有智能体编码时遵循。
## 一、基础信息
- **项目名称**: translator-agent
- **项目路径**: D:\Desktop\skill_translation_and_review
- **Python版本**: >= 3.12
- **包管理工具**: uv
## 二、常用命令
### 2.1 环境管理
```bash
# 创建虚拟环境
uv venv
# 激活虚拟环境 (Windows)
.venv\Scripts\activate
# 安装依赖
uv add <package>
# 从pyproject.toml安装所有依赖
uv install
```
### 2.2 运行程序
```bash
# 运行主程序
uv run python main.py
# 运行特定测试脚本
uv run python test/<测试目录>/scripts/<脚本名>.py
```
### 2.3 测试相关
```bash
# 目前无统一测试框架，单个脚本测试直接运行对应文件
# 例如测试Android迁移脚本
uv run python test/android-to-harmonyos-migration-workflow/scripts/migrate.py --help
```
## 三、代码风格规范
### 3.1 导入规范
1. 导入顺序：标准库 → 第三方库 → 本地模块
2. 每个导入单独一行，禁止合并导入
3. 避免使用`from module import *`通配符导入
4. 导入分组之间空一行分隔
```python
# 正确示例
import os
import logging
from typing import List, Dict
from langchain.chat_models import init_chat_model
```
### 3.2 命名规范
1. **变量/函数**: 蛇形命名法（snake_case）
   - 私有函数/变量以单下划线开头：`_private_function()`
   - 内部辅助函数以双下划线开头：`__internal_helper()`
2. **类**: 大驼峰命名法（PascalCase）
   - 例如：`CodeMigrator`, `FileProcessor`
3. **常量**: 全大写下划线分隔
   - 例如：`TARGET_EXTENSIONS`, `IMPORT_REPLACEMENTS`
4. **文件名**: 全小写，单词用下划线分隔
   - 例如：`migrate.py`, `compare_features.py`
### 3.3 类型注解
1. 所有函数必须添加类型注解，包括参数和返回值
2. 复杂类型使用`typing`模块：`List`, `Dict`, `Optional`, `Union`等
3. 避免使用`Any`类型，除非明确需要
```python
# 正确示例
def process_file(file_path: str, mode: str = 'auto') -> bool:
    """处理文件"""
    pass
```
### 3.4 注释规范
1. 每个函数/类必须有文档字符串，说明功能、参数、返回值
2. 中文注释优先，关键逻辑必须添加注释说明
3. 单行注释`# `后空一格，与代码至少空两格
4. 复杂算法/逻辑块前添加分段注释说明
```python
# 正确示例
# 统计目标文件总数，用于进度条显示
def _count_target_files_in_dir(root_path: str) -> int:
    """统计在给定根目录及其子目录中，符合 target_extensions 的文件数量。"""
    pass
```
### 3.5 代码格式
1. 缩进使用4个空格，禁止使用tab
2. 每行最大长度不超过120字符
3. 函数之间空两行，类方法之间空一行
4. 运算符前后各空一格，逗号后空一格
5. 括号内首尾无空格
```python
# 正确示例
result = calculate(a + b, c * d)
if x > 10 and y < 20:
    process()
```
### 3.6 错误处理
1. 必须捕获具体异常类型，禁止使用空`except:`
2. 异常信息必须包含足够上下文，便于排查
3. 使用`logging`模块记录错误，禁止`print`输出
4. 资源操作必须使用`with`语句或`try-finally`确保释放
```python
# 正确示例
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError as e:
    logging.error(f"文件不存在: {file_path} - {e}")
    return False
except UnicodeDecodeError as e:
    logging.error(f"文件编码错误: {file_path} - {e}")
    return False
```
### 3.7 字符串处理
1. 所有文件操作使用`utf-8`编码
2. 字符串拼接优先使用f-string，其次是`str.format()`
3. 路径操作优先使用`pathlib.Path`或`os.path`模块
4. 避免硬编码路径，使用配置或参数传入
## 四、项目特定规范
### 4.1 技能处理流程
1. 翻译流程：读取文件 → 调用LLM翻译 → 写入原文件
2. 审核流程：读取翻译后文件 → LLM审核 → 返回审核结果
3. 审核结果编码：
   - 1: 通过
   - 2: 有风险，需要人工检查
   - 3: 严重问题，需要重新翻译
### 4.2 支持的文件类型
```python
target_extensions = [
    ".txt", ".md", ".sh", ".html", ".json", ".xml", ".yaml",
    ".bat", ".cmd", ".js", ".php", ".css", ".py", ".java",
    ".c", ".cpp", ".cc", ".go", ".rs", ".cs", ".ts"
]
```
### 4.3 日志规范
1. 使用`logging`模块，级别分为INFO、WARNING、ERROR
2. 日志同时输出到文件（处理结果.log）和控制台
3. 日志格式：`"%(asctime)s - %(levelname)s - %(message)s"`
4. 每个文件处理完成必须记录结果
## 五、安全与禁忌
1. **禁止使用`rm`命令删除文件**，需要删除时使用`move`命令移动到`.trash`目录
2. **禁止使用`pip install`安装依赖到系统环境**，必须使用`uv add`或`uv pip install`在虚拟环境中操作
3. 禁止硬编码API密钥、密码等敏感信息，统一从环境变量读取
4. 禁止在代码中添加emoji表情，避免终端报错
5. 禁止使用Linux特定命令，所有脚本必须兼容Windows 10 x64系统
## 六、提交规范
1. 提交前确保代码无语法错误，功能正常
2. 提交信息简洁明了，说明修改内容
3. 禁止提交`.venv`、`.env`、日志文件等敏感或生成文件
4. 所有新增功能必须有对应的测试用例
## 七、参考文件
- 主程序实现：`main.py`
- 代码风格参考：`test/android-to-harmonyos-migration-workflow/scripts/migrate.py`
- 依赖配置：`pyproject.toml`
- 环境变量示例：`env.example`