.PHONY: doctor test test-python test-cpp format clean

PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

doctor:
	@./scripts/doctor.sh

test: test-python test-cpp

test-python:
	@$(PYTHON) -m unittest discover -s packages/python/so101-common/tests -v
	@$(PYTHON) -m unittest discover -s simulation/mujoco/tests -v

test-cpp:
	@./scripts/test_cpp.sh

format:
	@$(PYTHON) -m ruff format packages/python simulation/mujoco 2>/dev/null || true
	@find packages/cpp -type f \( -name '*.cpp' -o -name '*.hpp' \) -print0 | xargs -0 clang-format -i 2>/dev/null || true

clean:
	@cmake -E remove_directory build 2>/dev/null || true
