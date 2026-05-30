# Cowork-Specific Instructions

If you're in Cowork, the core workflow (draft → test → review → improve → repeat) is the same. Here's what changes:

## What works normally

- Subagents are available — spawn test cases and baselines in parallel as described in the main skill
- Description optimization (`run_loop.py` / `run_eval.py`) works fine since it uses `claude -p` via subprocess
- Packaging works — `package_skill.py` just needs Python and a filesystem
- If you hit severe timeout problems, run test prompts in series rather than parallel as a fallback

## What's different

**No browser/display** — use `--static <output_path>` with `generate_review.py`:

```bash
python <skill-builder-path>/eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  --static <workspace>/iteration-N/review.html
```

The script prints a `file://` URL — always include it in your response as a clickable markdown link:
`[Open Eval Viewer](file:///path/to/review.html)`

**Feedback collection** — since there's no running server, the viewer's "Submit All Reviews" button downloads `feedback.json` as a file. The user downloads it and you read it from there (you may need to request access).

**Generate the viewer before evaluating yourself** — in Cowork there's a tendency to skip the viewer and just self-evaluate. Don't. The human review is the point. Always run `generate_review.py` and give the user the link before making any changes. Put this in your TodoList: "Generate eval viewer and give user the link before revising skill."

## Updating an existing skill

If the user wants to update an installed skill (not create a new one):

- **Preserve the original name.** Note the skill's directory name and `name` frontmatter field — use them unchanged (e.g., `research-helper`, not `research-helper-v2`).
- **Copy to a writeable location before editing.** The installed skill path may be read-only. Copy to `/tmp/skill-name/`, edit there, and package from the copy.
- **Stage in `/tmp/` first** when packaging manually — direct writes may fail due to permissions.
