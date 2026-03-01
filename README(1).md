# Commands to run the ablation experiments

## Prerequisites

You must set at least one API key (recommended: OpenAI) before running.

### OpenAI (recommended)
```bash
export OPENAI_API_KEY="YOUR_KEY_HERE"
```

### Anthropic (optional fallback)
```bash
export ANTHROPIC_API_KEY="YOUR_KEY_HERE"
```

## Run experiments

All commands are run from:
```bash
cd SQL-of-Thought
```

### 1) Baseline (with correction loop)
```bash
python run_eval_single_schemalink.py --max-critic-attempts 3 --subset-size 20 --model gpt-4o-mini
```

### 2) Ablation (no correction loop)
```bash
python run_eval_single_schemalink.py --max-critic-attempts 0 --subset-size 20 --model gpt-4o-mini
```

## Outputs

Results will be saved to:

- `ablations_actual/20_gpt-4o-mini_max3.json`
- `ablations_actual/20_gpt-4o-mini_max0.json`
