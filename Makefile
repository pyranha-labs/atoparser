# Additional recipes for Python based development.
# Bootstrap python.mk once; from then on it pulls itself and other utilities whenever make runs.
ifeq ($(wildcard python.mk),)
python.mk:
	@tmp_dir="$$(mktemp -d)" && trap 'rm -rf "$$tmp_dir"' EXIT && \
		git clone --quiet --depth 1 --no-checkout --single-branch --branch $(or $(PY_MAKE_REF),main) \
			$(or $(PY_MAKE_REPO),git@github.com:pyranha-labs/build-tools.git) "$$tmp_dir" && \
		git -C "$$tmp_dir" show HEAD:python.mk > "$$tmp_dir/python.mk" && \
		install -m 444 "$$tmp_dir/python.mk" python.mk
endif
-include python.mk

##### Project Overrides #####

PYTHON_BIN := python3.12
UPSTREAM := git@github.com:pyranha-labs/atoparser.git

# Optional: Apply user overrides at the end to ensure user values override project overrides.
-include python_overrides.mk
