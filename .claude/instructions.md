# AI Model Guidelines

**CRITICAL RULES - CHECK BEFORE EVERY ACTION:**
- [ ] Am I about to run `git commit`? → STOP! Only use `git add` to stage files
- [ ] Am I about to run `git push`? → STOP! Never push to repository
- [ ] Am I making multiple changes at once? → Consider breaking into smaller steps
- [ ] Have I asked for approval before major changes? → Use text boxes for user feedback

## Core Workflow Rules

### 1. Test-Driven Development (TDD) - ALWAYS
1. **Write tests FIRST** - Never write implementation before tests
2. **Run tests to verify they FAIL** - Confirm test is actually testing something
3. **Write minimal code** to make tests pass
4. **Run tests again** to verify they pass
5. **Refactor** if needed, keeping tests green

### 2. Incremental Development
- Make the **smallest possible changes** per iteration
- One feature/fix at a time
- After each change: run tests, get feedback, proceed

### 3. Fast Feedback Loops
- Run tests after EVERY code change
- Use text boxes to ask for approval before:
  - Creating new files
  - Making architectural changes
  - Running git operations
- Always use Docker environment via `make` commands

### 4. Communication Style
- Be concise unless asked for details
- Focus on essential information only
- Let results speak (test output, coverage reports)

### 5. Git Workflow - STRICT RULES
**NEVER COMMIT OR PUSH**
- ✅ Allowed: `git status`, `git diff`, `git add`, `git checkout -b`
- ❌ Forbidden: `git commit`, `git commit --amend`, `git push`, `git rebase`
- After staging files with `git add`, **STOP and propose commit message**
- User will make the actual commit

### 6. Docker Environment
- Always run commands via `make` targets
- Never run tests/linting/formatting outside Docker
- Available commands: `make test`, `make lint`, `make format`, `make type`

### 7. Documentation
- Document architecture decisions in README.md
- Keep documentation updated with code changes
- Focus on "why" not just "what"

## Verification Checklist

Before completing any task, verify:
- [ ] Tests written first (TDD)
- [ ] All tests pass (`make test`)
- [ ] Code formatted (`make format-check`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make type`)
- [ ] Changes are minimal and focused
- [ ] Files are staged (not committed)
- [ ] Commit message proposed (but not executed)
- [ ] User has opportunity to review

## Project-Specific

1. This project contains documentation only with security relevant information
2. Documentation is in latex format
3. Use the `Makefile` to build the documents
