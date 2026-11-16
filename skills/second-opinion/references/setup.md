# ABOUTME: Prerequisites and troubleshooting for the second-opinion isolated Gemini Docker reviewer
# ABOUTME: Read when setting up the gemini-reviewer image/key or when the reviewer call fails

## Prerequisites

- `gemini-reviewer:latest` (built from `claude-forge/docker/isolated-gemini/`)
- API key file at `~/.config/gemini-api-key`, with access to `gemini-4-argon`

The `claude-reviewer` and `deepseek-reviewer` images are not used by this skill (advanced-review still uses them).

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "docker: command not found" | Docker Desktop must be running |
| Image not found | Build it: `docker/isolated-gemini/isolated-gemini-review.sh --build` |
| Gemini API errors | Check `~/.config/gemini-api-key` exists and is valid |
| Model not found | Check the key sees the model: `curl -s -H "x-goog-api-key: $(cat ~/.config/gemini-api-key)" 'https://generativelanguage.googleapis.com/v1beta/models?pageSize=200' \| jq -r '.models[].name' \| grep argon` must print `models/gemini-4-argon` |
| `429` / quota | The second opinion did not run; report it (SKILL.md Step 4). Do not switch model |
| Gemini "not running in a trusted directory" | Image predates the trust fix. Rebuild: `docker/isolated-gemini/isolated-gemini-review.sh --build` (the Dockerfile sets `GEMINI_CLI_TRUST_WORKSPACE=true`) |
| Timeout | Reduce context size; focus on the most relevant files |
| Gemini argues you're wrong, with evidence | You're probably wrong. Reconsider. |
