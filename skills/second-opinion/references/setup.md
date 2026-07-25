# ABOUTME: Prerequisites and troubleshooting for second-opinion isolated Docker reviewers (Claude, Gemini, DeepSeek)
# ABOUTME: Read when setting up second-opinion Docker images/auth or when reviewer calls fail

## Prerequisites

Images built and auth configured:
- `claude-reviewer:latest` (built from `claude-forge/docker/isolated-reviewer/`)
- `gemini-reviewer:latest` (built from `claude-forge/docker/isolated-gemini/`)
- `deepseek-reviewer:latest` (built from `claude-forge/docker/isolated-deepseek/`)
- Docker volume `claude-reviewer-auth` (populated via `docker run -it --rm -v claude-reviewer-auth:/home/node/.claude --entrypoint bash claude-reviewer:latest -c "claude login"`)
- API key file at `~/.config/gemini-api-key`
- API key file at `~/.config/deepseek-api-key`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "docker: command not found" | Docker Desktop must be running |
| Image not found | Build images: see Prerequisites |
| Claude auth fails | Re-login: `docker run -it --rm -v claude-reviewer-auth:/home/node/.claude --entrypoint bash claude-reviewer:latest -c "claude login"` |
| Claude `401` recurs across runs | The OAuth token in the volume expires periodically. Optional preflight before a run: `docker run --rm -v claude-reviewer-auth:/home/node/.claude:ro claude-reviewer:latest --print "ping"`; a non-zero/`401` means re-login first. Skip it for speed; structured degradation (Step 4) handles a mid-run `401` anyway. |
| Gemini API errors | Check `~/.config/gemini-api-key` exists and is valid |
| Gemini "not running in a trusted directory" | Image predates the trust fix. Rebuild: `docker/isolated-gemini/isolated-gemini-review.sh --build` (the Dockerfile sets `GEMINI_CLI_TRUST_WORKSPACE=true`) |
| DeepSeek "No API key found" | Check `~/.config/deepseek-api-key` exists and is valid; it is passed as `DEEPSEEK_API_KEY` |
| DeepSeek image not found | Build it: `docker/isolated-deepseek/isolated-deepseek-review.sh --build` |
| Timeout | Reduce context size; focus on the most relevant files |
| Both reviewers agree you're wrong | You're probably wrong. Reconsider. |
