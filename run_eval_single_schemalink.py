import json
import os
import argparse
from collections import defaultdict
from typing import List
from utils import *
import utils as utils_mod
from prompts import *
from analyze_by_subproblems import *
import difflib
import time

MAX_CRITIC_ATTEMPTS = 3

def evaluate(max_critic_attempts: int = MAX_CRITIC_ATTEMPTS, subset_size: int = 100, model: str = "gpt-4o-mini"):
    dev = load_spider(dev=True)
    taxonomy = json.load(open("error_taxonomy.json"))
    total, exact_match, valid_sql, exec_correct = 0, 0, 0, 0
    results = []
    seen = set() # seen samples in creating dataset for finetuning critic

    reset_llm_stats()
    run_start = time.perf_counter()
    sample_attempts = []

    for idx, item in enumerate(dev[:subset_size]):
        sample_start = time.perf_counter()
        print("\n--- Sample", idx + 1, "---")
        question = item['question']
        gold_sql = item['query']
        db_id = item['db_id']

        schema = load_schema(db_id)

        entry = {
            "question": question,
            # "gold_sql": gold_sql,
            "db_id": db_id,
            "agents": {}
        }

        # 1. Schema Agent
        schema_prompt = alt_schema_linking_agent_prompt(question, schema)
        # print("[Schema Agent Prompt]\n", schema_prompt)
        corrected_schema = call_agent(schema_prompt, model)
        print("[Schema Agent Output]\n", corrected_schema)
        # entry["agents"]["schema"] = {"prompt": schema_prompt, "output": corrected_schema}

        # 2. Subproblem Agent
        subproblem_prompt = subproblem_agent_prompt(question, corrected_schema)
        print("[Subproblem Agent Prompt]\n", subproblem_prompt)
        sub_json = clean_json(call_agent(subproblem_prompt, model))
        print("[Subproblem Agent Output]\n", sub_json)
        # entry["agents"]["subproblem"] = {"prompt": subproblem_prompt, "output": sub_json}

        subproblem_specific_clauses = list(set(parse_subproblems(sub_json)))
        subprob_plan, subprob_sql = clause_specific_prompts(subproblem_specific_clauses)

        # 3. Query Plan Agent
        plan_prompt = query_plan_agent_prompt(question, corrected_schema, sub_json)
        # plan_prompt = query_plan_agent_prompt(question, schema, sub_json, subprob_plan)
        # print("[Query Plan Agent Prompt]\n", plan_prompt)
        plan = call_agent(plan_prompt, model)
        print("[Query Plan Agent Output]\n", plan)
        # entry["agents"]["plan"] = {"prompt": plan_prompt, "output": plan}

        # 4. SQL Generating Agent
        sql_prompt = sql_agent_prompt(question, plan, corrected_schema)
        # sql_prompt = sql_agent_prompt(plan, schema, subprob_sql)
        # print("[SQL Agent Prompt]\n", sql_prompt)
        sql = call_agent(sql_prompt, model)
        sql = postprocess_sql(sql)
        print("[SQL Agent Output]\n", sql)

        exec_match, error = query_execution(item, sql)
        exec_failed = not(exec_match)
        attempts = 0

        # Correction Loop
        
        while exec_failed and attempts < max_critic_attempts:
            correction_plan_prompt = correction_plan_agent_prompt(question, sql, corrected_schema, error)
            correction_plan = call_agent(correction_plan_prompt, model)
            # print(f"\n[SQL Correction Plan Prompt]: \n{correction_plan_prompt}")
            print(f"\n[SQL Correction Plan Output]: \n{correction_plan}")
            correction_sql_prompt = correction_sql_agent_prompt(question, corrected_schema, correction_plan, sql)
            corrected_sql = call_agent(correction_sql_prompt, model)
            sql = postprocess_sql(corrected_sql)
            # print(f"\n[SQL Correction Prompt]: \n{correction_sql_prompt}")
            print(f"\n[SQL Correction Output]: \n{sql}")
            exec_match, error = query_execution(item, sql)
            exec_failed = not(exec_match)
            attempts += 1
            print(f"\nVALID SQL?: {exec_match}, \nWill loop continue? {exec_failed}, {attempts}")

        entry["critic_attempts"] = attempts
        sample_attempts.append(attempts)
        
        ''' commenting critic loop
        critic_history = []
        attempts = 0

        while exec_failed and attempts < MAX_CRITIC_ATTEMPTS:
            valid, errors = check_valid_critic_and_push_error(sql, question, db_id, corrected_schema, taxonomy)
            critic_history.append(errors)
            if not valid:
                for error_code in errors:
                    key = (question, sql, error_code)
                    if key in seen: continue
                    seen.add(key)
                    out = {
                        "question": question,
                        "incorrect_sql": sql,
                        "error_code": error_code,
                        "explanation": taxonomy.get(error_code, ""),
                        "gold_sql": gold_sql
                    }
                    with open("critic_data.jsonl", "a", encoding="utf-8") as fout:
                        fout.write(json.dumps(out, ensure_ascii=False) + "\n")

        entry["agents"]["critic"] = [{
            "initial_sql": sql, "critic_history": critic_history,
            "exec_success": not exec_failed
        }]
        '''
        
        # Metric 1: Exact Match
        gold_sql = postprocess_sql(gold_sql)
        entry["gold_sql"] = gold_sql
        entry["gen_sql"] = sql
        print(f"Gold SQL: {gold_sql}\n Generated SQL: {sql}\n")
        if sql.strip().lower() == gold_sql.strip().lower():
            exact_match += 1
            entry["exact_match"] = True
        else:
            entry["exact_match"] = False

        # Metric 2: Valid SQL
        gen_rows, gen_err = exec_query(utils_mod._spider_db_path(db_id), sql)
        entry["valid_sql"] = gen_err is None
        if gen_err is None:
            valid_sql += 1

        # Metric 3: Execution Accuracy

        entry["exec_match"] = exec_match
        if exec_match: 
            exec_correct += 1
        ea = entry["exec_match"]
        print(f"\n Execution Match: {ea}\n")
        total += 1
        entry["sample_seconds"] = time.perf_counter() - sample_start
        results.append(entry)

        print(f"Total: {total}")
        print(f"Exact Match: {exact_match}/{total} = {exact_match/total:.2%}")
        print(f"Valid SQL: {valid_sql}/{total} = {valid_sql/total:.2%}")
        print(f"Execution Accuracy: {exec_correct}/{total} = {exec_correct/total:.2%}")
    
    llm_stats = get_llm_stats()
    run_seconds = time.perf_counter() - run_start

    summary = {
        "total": total,
        "exact_match": exact_match,
        "valid_sql": valid_sql,
        "execution_accuracy": exec_correct,
        "exact_match_rate": round(exact_match / total, 4),
        "valid_sql_rate": round(valid_sql / total, 4),
        "execution_accuracy_rate": round(exec_correct / total, 4),
        "max_critic_attempts": max_critic_attempts,
        "total_llm_calls": int(llm_stats.get("calls", 0)),
        "total_llm_seconds": round(float(llm_stats.get("seconds", 0.0)), 4),
        "total_run_seconds": round(run_seconds, 4),
        "avg_run_seconds_per_sample": round(run_seconds / total, 4) if total else None,
        "avg_llm_calls_per_sample": round(llm_stats.get("calls", 0) / total, 4) if total else None,
        "avg_critic_attempts_per_sample": round(sum(sample_attempts) / total, 4) if total else None
    }

    output = {
        "summary": summary,
        "results": results
    }

    os.makedirs("ablations_actual", exist_ok=True)
    out_path = f"ablations_actual/{subset_size}_{model}_max{max_critic_attempts}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print("\n======= Evaluation Summary =======")
    print(json.dumps(summary, indent=2))

    print(f"Total: {total}")
    print(f"Exact Match: {exact_match}/{total} = {exact_match/total:.2%}")
    print(f"Valid SQL: {valid_sql}/{total} = {valid_sql/total:.2%}")
    print(f"Execution Accuracy: {exec_correct}/{total} = {exec_correct/total:.2%}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-critic-attempts", type=int, default=MAX_CRITIC_ATTEMPTS)
    parser.add_argument("--subset-size", type=int, default=100)
    parser.add_argument("--model", type=str, default="gpt-4o-mini")
    args = parser.parse_args()

    evaluate(max_critic_attempts=args.max_critic_attempts, subset_size=args.subset_size, model=args.model)
