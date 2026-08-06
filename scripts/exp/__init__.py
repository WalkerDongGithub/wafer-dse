"""论文实验模块。

每个 exp_*.py 是一个独立的实验 batch，调用 UnifiedLp 批量求解，
将结果写入 CSV 到 outputs/paper_experiments/。

使用方式:
    python -m scripts.exp.exp_scalability
    python -m scripts.exp.exp_constraint_coupling
"""
