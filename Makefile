.PHONY: doctor test test-python test-cpp format clean

doctor:
	@./scripts/doctor.sh

test: test-python test-cpp

test-python:
	@python3 -m unittest discover -s packages/python/so101-common/tests -v

test-cpp:
	@./scripts/test_cpp.sh

format:
	@python3 -m ruff format packages/python 2>/dev/null || true
	@find packages/cpp -type f \( -name '*.cpp' -o -name '*.hpp' \) -print0 | xargs -0 clang-format -i 2>/dev/null || true

clean:
	@cmake -E remove_directory build 2>/dev/null || true
