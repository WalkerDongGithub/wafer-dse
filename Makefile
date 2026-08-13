# wafer-dse 实验运行入口 (V2 LP 引擎)
#
#   make help            打印本帮助（默认目标）
#   make test            全部测试 (tests/ 下 11 个 .md，叙述 + 可运行代码块)
#   make matrix          实验矩阵 → exp/output/matrix_<组>.csv  [PARAMS=...]
#   make ledger          约束账本  [TOPOS="Mesh(2) Dragonfly(2,1,1)"]
#   make smoke           快速冒烟 (~半分钟)
#   make run             CLI：读 YAML 配置求解  [PROBLEM=config/problems/xxx.yaml]
#   make clean           清 __pycache__

.PHONY: help test matrix ledger smoke run clean

PYTHON = python3
PARAMS ?= ucie-32g      # toy | ucie-16g | ucie-24g | ucie-32g
TOPOS ?=
PROBLEM ?= config/problems/toy_fullmesh2.yaml

# ------------------------------------------------------------------
# 测试
# ------------------------------------------------------------------

test:
	cd tests && PYTHONPATH=../src $(PYTHON) run_all.py

# ------------------------------------------------------------------
# 实验
# ------------------------------------------------------------------

matrix:
	PYTHONPATH=src $(PYTHON) exp/run_matrix.py $(PARAMS)

ledger:
	PYTHONPATH=src $(PYTHON) exp/run_ledger.py $(TOPOS)

smoke:
	cd exp && PYTHONPATH=../src $(PYTHON) smoke_bmax.py

run:
	PYTHONPATH=src $(PYTHON) src/main.py $(PROBLEM)

# ------------------------------------------------------------------
# 元操作
# ------------------------------------------------------------------

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -exec rm -f {} + 2>/dev/null || true

help:
	@grep -E "^#   " $(MAKEFILE_LIST) | sed 's/^#   //'
