"""Main entry point for the chat application."""
import sys
import json
import os
import logging
import random
from datetime import datetime
from config import Config
from chat_client import ChatClient

def setup_logging(timestamp):
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    log_file = os.path.join('logs', f'turing_test_{timestamp}.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file

def create_progress_bar(progress, total_width=50):
    """Create a progress bar string."""
    filled_width = int(total_width * progress / 100)
    bar = '=' * (filled_width - 1)
    if progress < 100:
        bar += '>'
    bar = bar.ljust(total_width, ' ')
    return f"[{bar}] {progress:>3.0f}%"

def read_questions(file_path: str) -> list[str]:
    """Read questions from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        questions = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):  # 忽略空行和注释行
                questions.append(line)
        return questions

def get_judge_answer(question: str, answer1: str, answer2: str, round_info: str) -> bool:
    """Get judge's decision on which answer is from a human."""
    while True:
        print(f"\n{round_info}")
        print(f"问题: {question}")
        print(f"回答 1: {answer1}")
        print(f"回答 2: {answer2}")
        try:
            choice = int(input("输入1或2来选择哪个是人类的回答: ").strip())
            if choice in [1, 2]:
                return choice
            print("请只输入1或2！")
        except ValueError:
            print("请只输入1或2！")

def get_human_answer_with_name(question: str, participant_name: str) -> str:
    """Get answer from human input."""
    print("\n请回答这个问题:")
    print(f"Q: {question}")
    print(f"({participant_name}): A: ", end='')
    return input().strip()

def main():
    """Run the main application."""
    try:
        # Set console encoding to UTF-8
        if sys.platform == 'win32':
            sys.stdout.reconfigure(encoding='utf-8')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = setup_logging(timestamp)
        logging.info("=== 图灵测试开始 ===")
        
        print("\n欢迎来到图灵测试！")
        
        config = Config()
        client = ChatClient(config)
        
        logging.info(f"配置加载完成: {len(config.models)} 个模型")
        for model in config.models:
            logging.info(f"已加载模型: {model}")
        
        questions = read_questions('questions.txt')
        logging.info(f"问题加载完成: {len(questions)} 个问题")
        for i, q in enumerate(questions, 1):
            logging.info(f"问题 {i}: {q}")
        
        # Store results for each model
        all_model_results = {}
        all_ai_answers = {}
        all_human_answers = [] # To store all human answers from multiple rounds
        all_human_names = [] # To store names of all participants
        
        # First pass: Get AI answers
        print("\n=== 第一轮：AI作答 ===")
        logging.info("\n=== 第一轮：AI作答 ===")
        for model in config.models:
            logging.info(f"模型 {model} 开始回答")
            print(f"\n正在获取 {model} 的回答...")
            client.set_model(model)  # Set the current model
            answers = []
            for i, question in enumerate(questions, 1):
                print(f"问题 {i}/{len(questions)}...")
                answer = client.get_completion(question)
                answers.append(answer)
                logging.info(f"问题 {i} - {model} 回答: {answer}")
            
            print(f"{model} 已完成所有问题")
            all_ai_answers[model] = answers
        
        # Second pass: Get human answers (allow multiple rounds)
        print("\n=== 第二轮：人类作答 ===")
        print("每一轮将由不同的人类参与者回答所有问题。")
        logging.info("\n=== 第二轮：人类作答 ===")
        
        human_round = 0
        continue_human_rounds = 'y'
        
        while continue_human_rounds.lower() == 'y':
            human_round += 1
            print(f"\n--- 第 {human_round} 轮人类作答 ---")
            participant_name = input("\n请输入本轮参与者姓名: ").strip()
            all_human_names.append(participant_name)
            
            logging.info(f"\n=== 第 {human_round} 轮人类作答 ===")
            logging.info(f"参与者: {participant_name}")
            
            human_answers_round = []
            for i, question in enumerate(questions, 1):
                print(f"\n问题 {i}/{len(questions)}")
                answer = get_human_answer_with_name(question, participant_name)
                human_answers_round.append(answer)
                logging.info(f"问题 {i} - {participant_name} 回答: {answer}")
            
            all_human_answers.append({
                "participant": participant_name,
                "answers": human_answers_round
            })
            
            print(f"\n{participant_name} 的回答已记录完成！")
            while True:
                continue_human_rounds = input("\n是否继续下一轮人类作答？(y/n): ").strip().lower()
                if continue_human_rounds in ['y', 'n']:
                    break
                print("请只输入 y 或 n！")
            logging.info(f"是否继续人类作答: {continue_human_rounds}")
        
        logging.info(f"第二轮结束，共有 {len(all_human_names)} 位参与者: {', '.join(all_human_names)}")
        
        # Third pass: Judge each model separately
        logging.info("\n=== 第三轮：判断测试 ===")
        print("\n=== 第三轮：判断测试 ===")
        for model_idx, model in enumerate(config.models, 1):
            logging.info(f"开始第 {model_idx}/{len(config.models)} 轮测试: 人类 vs {model}")
            print(f"\n第 {model_idx}/{len(config.models)} 轮测试")
            print(f"人类 vs {model}")
            print("-" * 50)
            
            results = []
            ai_answers = all_ai_answers[model]
            
            for i, (question, ai_answer) in enumerate(zip(questions, ai_answers), 1):
                # Get all human answers for this question
                human_answers_for_question = [round_data["answers"][i-1] for round_data in all_human_answers]
                human_answer = random.choice(human_answers_for_question)
                
                # Randomly swap AI and human answers
                is_swapped = random.random() < 0.5
                answer1 = ai_answer if is_swapped else human_answer
                answer2 = human_answer if is_swapped else ai_answer
                
                round_info = f"问题 {i}/{len(questions)} - 人类 vs {model}"
                judge_choice = get_judge_answer(question, answer1, answer2, round_info)
                is_correct = (judge_choice == 2) if is_swapped else (judge_choice == 1)
                
                # Log the judging details
                logging.info(f"问题 {i} 判断详情:")
                logging.info(f"  问题: {question}")
                logging.info(f"  回答1 ({'AI' if is_swapped else '人类'}): {answer1}")
                logging.info(f"  回答2 ({'人类' if is_swapped else 'AI'}): {answer2}")
                logging.info(f"  判断选择: {judge_choice}")
                logging.info(f"  判断正确: {'是' if is_correct else '否'}")
                
                results.append({
                    "question": question,
                    "human_answer": human_answer,
                    "ai_answer": ai_answer,
                    "judge_choice": judge_choice,
                    "correct": is_correct,
                    "model": model,
                    "is_swapped": is_swapped
                })
            
            all_model_results[model] = results
            
            # Show and log interim results for this model
            correct_count = sum(1 for r in results if r['correct'])
            accuracy = (correct_count/len(questions))*100
            
            result_summary = f"""
{model} 判断结果:
总题数: {len(questions)}
正确判断: {correct_count}
正确率: {accuracy:.1f}%"""
            
            print(result_summary)
            logging.info(result_summary)
            print("-" * 50)
        
        # Save detailed comparison log
        output_file = f'comparison_{timestamp}.txt'
        logging.info(f"保存详细对比记录到: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            # First write participant information
            f.write("=== 人类参与者 ===\n")
            for i, name in enumerate(all_human_names, 1):
                f.write(f"{i}. {name}\n")
            
            # Then write model comparisons
            for model, results in all_model_results.items():
                f.write(f"\n\n=== 模型: {model} ===\n")
                for i, result in enumerate(results, 1):
                    f.write(f"\n问题 {i}:\n")
                    f.write(f"Q: {result['question']}\n")
                    f.write(f"人类回答: {result['human_answer']}\n")
                    f.write(f"AI回答 ({model}): {result['ai_answer']}\n")
                    f.write(f"判断选择: {result['judge_choice']}\n")
                    f.write(f"判断正确: {'是' if result['correct'] else '否'}\n")
                    f.write("-" * 80 + "\n")
        
        # Save results in JSON format
        result_file = f'results_{timestamp}.json'
        logging.info(f"保存判断结果到: {result_file}")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "total_questions": len(questions),
                "participants": all_human_names,
                "models": {
                    model: {
                        "model_name": model,
                        "correct_guesses": sum(1 for r in results if r['correct']),
                        "accuracy": sum(1 for r in results if r['correct']) / len(questions),
                        "results": [{
                            "question_id": i,
                            "correct": r['correct'],
                            "judge_choice": r['judge_choice'],
                            "is_swapped": r['is_swapped']
                        } for i, r in enumerate(results, 1)]
                    }
                    for model, results in all_model_results.items()
                }
            }, f, ensure_ascii=False, indent=2)
        
        # Show final summary
        print("\n=== 最终结果统计 ===")
        logging.info("\n=== 最终结果统计 ===")
        for model, results in all_model_results.items():
            correct = sum(1 for r in results if r["correct"])
            print(f"\n{model}:")
            print(f"正确判断: {correct}/{len(results)}")
            print(f"正确率: {(correct/len(results))*100:.1f}%")
            
            logging.info(f"\n{model}:")
            logging.info(f"正确判断: {correct}/{len(results)}")
            logging.info(f"正确率: {(correct/len(results))*100:.1f}%")
        
        # 生成结论文件
        conclusion_file = f"conclusion_{timestamp}.md"
        with open(conclusion_file, "w", encoding="utf-8") as f:
            f.write("# 图灵测试结果分析报告\n")
            f.write(f"测试时间：{timestamp}\n\n")
            
            f.write("## 测试说明\n")
            f.write("本次图灵测试采用20个开放性问题，由人类和AI分别回答，然后由第二位人类判断哪个是人类的回答。")
            f.write("如果判断者超过50%将AI的回答误判为人类回答，则认为该AI通过了图灵测试。\n\n")
            
            f.write("## 测试结果\n\n")
            for model, results in all_model_results.items():
                correct = sum(1 for r in results if r["correct"])
                total = len(results)
                ai_mistaken_as_human = sum(1 for r in results if r["judge_choice"] == 1 and not r["correct"])
                ai_human_rate = (ai_mistaken_as_human/total) * 100  # AI被判断为人类的比率
                human_human_rate = (correct/total) * 100            # 人类被判断为人类的比率
                
                f.write(f"### {model}\n")
                f.write("- 命中率分析：\n")
                f.write(f"  - AI回答被判断为人类：{ai_human_rate:.1f}%\n")
                f.write(f"  - 人类回答被判断为人类：{human_human_rate:.1f}%\n")
                
                if ai_human_rate > 50:
                    conclusion = "通过图灵测试"
                    if ai_human_rate > 90:
                        conclusion = "完全通过图灵测试"
                    elif ai_human_rate > 70:
                        conclusion = "显著通过图灵测试"
                else:
                    conclusion = "未通过图灵测试"
                
                f.write(f"- 结论：{conclusion}\n\n")
            
            f.write("## 总体结论\n")
            passed_models = []
            for model, results in all_model_results.items():
                ai_mistaken_as_human = sum(1 for r in results if r["judge_choice"] == 1 and not r["correct"])
                ai_human_rate = (ai_mistaken_as_human/len(results)) * 100
                if ai_human_rate > 50:
                    passed_models.append(model)
            
            if passed_models:
                f.write(f"1. 共有 {len(passed_models)} 个模型通过了图灵测试：{', '.join(passed_models)}\n")
            else:
                f.write("1. 没有模型通过图灵测试\n")
            
            f.write(f"2. 测试参与者：{len(all_human_names)} 位\n")
            f.write(f"3. 测试问题数量：{len(questions)} 个\n")
        
        logging.info(f"\n结论文件已保存到: {conclusion_file}")
        print(f"\n结论文件已保存到: {conclusion_file}")
        
        logging.info("=== 图灵测试结束 ===")
        print("\n=== 图灵测试结束 ===")
        
    except Exception as e:
        error_msg = f"错误: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        raise

if __name__ == "__main__":
    main()
