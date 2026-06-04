.PHONY: test test-quiet test-one test-hungarian test-derangement test-topology \
        test-solver test-model run clean lint

PYTHON = python
PYTHONPATH = PYTHONPATH=src

# ------------------------------------------------------------------
# 测试
# ------------------------------------------------------------------

test:
	$(PYTHONPATH) $(PYTHON) -m pytest tests/ -v

test-quiet:
	$(PYTHONPATH) $(PYTHON) -m pytest tests/ -q

test-one:
	$(PYTHONPATH) $(PYTHON) -m pytest tests/$(TEST) -v

test-hungarian:
	$(PYTHONPATH) $(PYTHON) -m pytest tests/test_hungarian.py tests/test_derangement.py -v

test-topology:
	$(PYTHONPATH) $(PYTHON) -m pytest tests/test_topology_*.py -v

test-solver:
	$(PYTHONPATH) $(PYTHON) -m pytest tests/test_solver_*.py -v

test-model:
	$(PYTHONPATH) $(PYTHON) -m pytest tests/test_model.py -v

test-slow:
	$(PYTHONPATH) $(PYTHON) -m pytest tests/ -v --durations=10

# ------------------------------------------------------------------
# 运行
# ------------------------------------------------------------------

run:
	$(PYTHONPATH) $(PYTHON) -m wafer_dse --config configs/example_user_request.yaml

# ------------------------------------------------------------------
# 元操作
# ------------------------------------------------------------------

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '.DS_Store' -exec rm -f {} + 2>/dev/null || true
	find . -name '*.pyc' -exec rm -f {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf outputs/

lint:
	$(PYTHONPATH) $(PYTHON) -m flake8 src/wafer_dse/ --max-line-length=120 || true
