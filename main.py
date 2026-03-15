import os
import logging
import dotenv
from langchain.chat_models import init_chat_model

# Optional progress bar support
try:
    from tqdm import tqdm  # type: ignore
except Exception:
    tqdm = None  # tqdm not installed; fall back to no-progress mode

# Global progress bar handle (initialized in main)
progress_bar = None

dotenv.load_dotenv()

#####################################################################

# 【模型配置与提示词加载】
llm = init_chat_model(
    base_url=os.getenv("LLM_BASE_URL"),
    model=os.getenv("LLM_MODEL_NAME"),
    model_provider="openai",
    api_key=os.getenv("LLM_API_KEY"),
    temperature=0.2,
)
with open("./prompt/translate_sys_prompt.txt", "r", encoding="utf-8") as f:
    translate_system_prompt = f.read()
with open("./prompt/review_sys_prompt.txt", "r", encoding="utf-8") as f:
    review_system_prompt = f.read()

#####################################################################

# 【日志初始化】
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("处理结果.log"), logging.StreamHandler()],
)
success_count = 0
fail_count = 0
total_count = 0
# 存储所有审核结果，以便最终输出到CSV
audit_results = []

#####################################################################


# 【文件翻译】
def _translate_skill(file_path, translate_system_prompt=translate_system_prompt):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    messages = [
        {"role": "system", "content": translate_system_prompt},
        {"role": "user", "content": content},
    ]
    response = llm.invoke(messages)

    # 将返回内容强制转换为字符串再写入文件，避免类型不确定导致写入失败
    translated = str(response.content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(translated)


#####################################################################


# 【文件审核】
def _review_skill(file_path, review_system_prompt=review_system_prompt):
    # 使用绝对路径打开系统提示文件
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        messages = [
            {"role": "system", "content": review_system_prompt},
            {"role": "user", "content": content},
        ]
        response = llm.invoke(messages)

        # LLM应返回1、2、3（其中1为通过，2为有风险，3为严重问题）
        first = str(response.content[0])
        if first == "1":
            return {"code": "1", "reason": ""}
        elif first == "2":
            return {"code": "2", "reason": str(response.content)}
        elif first == "3":
            return {"code": "3", "reason": str(response.content)}
        else:
            # 未识别的返回，默认标记为风险
            return {"code": "2", "reason": str(response.content)}
    except Exception as e:
        # 日志中记录异常并返回默认的风险结果
        logging.error(f"审核异常: {file_path} - {e}")
        return {"code": "2", "reason": f"审核异常: {e}"}


#####################################################################

# 【主程序 - 遍历路径循环处理】
target_extensions = [  # 支持的文件扩展名列表
    ".txt",
    ".md",
    ".sh",
    ".html",
    ".json",
    ".xml",
    ".yaml",
    ".bat",
    ".cmd",
    ".js",
    ".php",
    ".css",
    ".py",
    ".java",
    ".c",
    ".cpp",
    ".cc",
    ".go",
    ".rsj",
    ".cs",
    ".toon",
    ".ts",
]


def _count_target_files_in_dir(root_path: str) -> int:
    """统计在给定根目录及其子目录中，符合 target_extensions 的文件数量。"""
    count = 0
    for dirpath, dirnames, filenames in os.walk(root_path):
        for fname in filenames:
            if os.path.splitext(fname)[1] in target_extensions:
                count += 1
    return count


# 递归法处理(并写入日志)
def process_file_list(file_list, current_path="."):
    global success_count, fail_count, total_count
    for i in file_list:
        full_path = os.path.join(current_path, i)
        absolute_path = os.path.abspath(full_path)
        if os.path.isfile(absolute_path):
            # 仅对符合扩展名的目标文件进行处理，其他文件跳过但不统计进度
            if os.path.splitext(i)[1] in target_extensions:
                # 先翻译再审核，并记录审核结果
                try:
                    _translate_skill(absolute_path)
                    review_res = _review_skill(absolute_path)
                    audit_results.append(
                        (
                            absolute_path,
                            review_res.get("code", ""),
                            review_res.get("reason", ""),
                        )
                    )
                    logging.info(
                        f"翻译完成并执行审核: {absolute_path} -> 结果 {review_res.get('code', '')}"
                    )
                    success_count += 1
                except Exception as e:
                    logging.error(f"处理异常: {absolute_path} - {e}")
                    fail_count += 1
                # 使用 tqdm 的输出，避免打断进度条显示
                if progress_bar is not None:
                    if tqdm is not None and hasattr(tqdm, "write"):
                        tqdm.write(absolute_path)
                    else:
                        print(absolute_path)
                    progress_bar.update(1)
                else:
                    print(absolute_path)

            else:
                logging.info(f"跳过文件（不在支持的扩展名列表中）: {absolute_path}")
                fail_count += 1
        elif os.path.isdir(absolute_path):
            process_file_list(os.listdir(absolute_path), absolute_path)


#####################################################################


def main():
    file_path = input("请输入文件路径: ")
##    file_path = r"D:\Desktop\skill_translation_and_review\test"  # 测试用

    os.chdir(file_path)
    file_list = os.listdir()
    # 初始化进度条（若 tqdm 可用）并在处理前统计目标文件总数
    global progress_bar
    total_target = _count_target_files_in_dir(file_path)
    if tqdm is not None:
        progress_bar = tqdm(total=total_target, desc="处理中", unit="文件")
    else:
        progress_bar = None
    try:
        process_file_list(file_list)
    finally:
        if progress_bar is not None:
            progress_bar.close()
            progress_bar = None
    logging.info(
        f"处理完成 - 总文件数: {total_count}, 成功: {success_count}, 失败/跳过: {fail_count}"
    )
    # 将审核结果写入CSV，文件名为审核结果.csv，保存在当前工作目录，UTF-8编码
    csv_path = os.path.join(os.getcwd(), "审核结果.csv")
    try:
        import csv

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            for row in audit_results:
                writer.writerow([row[0], row[1], row[2]])
        logging.info(f"审核结果CSV已写入: {csv_path}")
    except Exception as e:
        logging.error(f"写入审核结果CSV失败: {e}")


if __name__ == "__main__":
    main()
