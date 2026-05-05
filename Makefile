# dotagents Makefile
# Installs skills, agents, and Pi extensions for AI coding agents
#
# Run `make install` to build and install.
# Requires Python 3.11+.

PYTHON := python3
BUILD_SCRIPT := $(CURDIR)/scripts/build.py
INSTALL_ARGS :=
ifeq ($(FORCE),1)
INSTALL_ARGS += --force
endif

.PHONY: all install install-skills install-extensions build typecheck clean help check-python

all: help

help:
	@echo "dotagents - Skills and Extensions Installer"
	@echo ""
	@echo "Usage:"
	@echo "  make install            Build and install skills, agents, and Pi extensions"
	@echo "  make install FORCE=1    Force install and initialize/reset manifest"
	@echo "  make install-skills     Install skills only"
	@echo "  make install-extensions Install Pi extensions only"
	@echo "  make build              Build skills, agents, and Pi extensions"
	@echo "  make typecheck          Type-check Pi extensions"
	@echo "  make clean              Remove installed artifacts and build artifacts"
	@echo "  make help               Show this help message"
	@echo ""
	@echo "Install paths:"
	@echo "  Claude Code:           ~/.claude/skills/"
	@echo "  OpenCode/Pi/Codex:     ~/.agents/skills/"
	@echo "  Pi Subagents:          ~/.pi/agent/agents/"
	@echo "  Pi Extensions:         ~/.pi/agent/extensions/"

check-python:
	@$(PYTHON) -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null || \
		(echo "Error: Python 3.11+ required"; exit 1)

install: check-python
	@$(PYTHON) $(BUILD_SCRIPT) install $(INSTALL_ARGS)
	@echo "All skills, agents, and Pi extensions installed"

build: check-python
	@$(PYTHON) $(BUILD_SCRIPT) build

typecheck:
	@pnpm typecheck

install-skills: check-python
	@$(PYTHON) $(BUILD_SCRIPT) install-skills $(INSTALL_ARGS)

install-extensions: check-python
	@$(PYTHON) $(BUILD_SCRIPT) install-extensions $(INSTALL_ARGS)

clean: check-python
	@$(PYTHON) $(BUILD_SCRIPT) clean
