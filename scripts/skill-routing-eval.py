#!/usr/bin/env python3
# ABOUTME: Builds the skill-routing judge prompt from live SKILL.md descriptions and scores a judge's answers
# ABOUTME: build = emit prompt for the judge; score = compare judge JSON against cases.jsonl, print accuracy and confusions

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
EVAL = ROOT / "quality_reports" / "evals" / "skill-routing"
CASES = EVAL / "cases.jsonl"  # overridden by --cases


def descriptions() -> dict[str, str]:
    """name -> description, parsed from the frontmatter of every SKILL.md."""
    out = {}
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = path.read_text()
        parts = text.split("---")
        if len(parts) < 3:
            continue
        fm = parts[1]
        m = re.search(r'^description:\s*(.+?)(?=^\w[\w-]*:\s|\Z)', fm, re.S | re.M)
        if not m:
            continue
        desc = " ".join(m.group(1).split()).strip().strip('"')
        out[path.parent.name] = desc
    return out


def load_cases(path: Path | None = None) -> list[dict]:
    src = path or CASES
    return [json.loads(line) for line in src.read_text().splitlines() if line.strip()]


def build(cases_path: Path | None = None) -> str:
    descs = descriptions()
    catalog = "\n".join(f"- {n}: {d}" for n, d in descs.items())
    cases = load_cases(cases_path)
    prompts = "\n".join(f'{c["id"]}. {c["prompt"]}' for c in cases)
    return f"""You are routing user requests to skills. Below is the full skill catalog, exactly as an agent sees it: a name and a description each.

CATALOG ({len(descs)} skills)
{catalog}

REQUESTS
{prompts}

For each numbered request, pick the ONE skill whose description best fits, or the literal string "none" if no skill applies and the agent should just do the work directly.

Judge only from the descriptions above. Do not use outside knowledge about what these skills contain. If two descriptions fit equally well, pick the one you would actually invoke and say so by listing the runner-up.

Return ONLY a JSON array, no prose, one object per request:
[{{"id": 1, "choice": "<skill name or none>", "runner_up": "<skill name or none>"}}]
"""


def one_case_prompt(catalog: str, prompt: str) -> str:
    """One request, no siblings: the judge cannot infer how many negatives to expect."""
    return f"""You are routing a user request to a skill. Below is the full skill catalog, exactly as an agent sees it: a name and a description each.

CATALOG
{catalog}

REQUEST
{prompt}

Pick the ONE skill whose description best fits, or the literal string "none" if no skill applies and the agent should just do the work directly.

Judge only from the descriptions above. Do not use outside knowledge about what these skills contain.

Return ONLY a JSON object, no prose:
{{"choice": "<skill name or none>", "runner_up": "<skill name or none>"}}
"""


def ask_gemini(prompt: str, model: str, key: str) -> dict:
    import urllib.error
    import urllib.request

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as e:
        return {"choice": f"HTTP_{e.code}", "runner_up": e.read()[:200].decode(errors="replace")}
    text = payload["candidates"][0]["content"]["parts"][0]["text"]
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {"choice": "UNPARSEABLE", "runner_up": text[:120]}
    return json.loads(m.group(0))


def run_per_case(cases_path: Path | None, model: str, out: Path) -> int:
    """One judge call per case, in parallel. Removes the batch-composition bias."""
    import os
    from concurrent.futures import ThreadPoolExecutor

    key = os.environ.get("GEMINI_API_KEY") or Path.home().joinpath(".config/gemini-api-key").read_text().strip()
    descs = descriptions()
    catalog = "\n".join(f"- {n}: {d}" for n, d in descs.items())
    cases = load_cases(cases_path)

    def work(case: dict) -> dict:
        answer = ask_gemini(one_case_prompt(catalog, case["prompt"]), model, key)
        return {"id": case["id"], "choice": answer.get("choice", "MISSING"), "runner_up": answer.get("runner_up", "")}

    with ThreadPoolExecutor(max_workers=6) as pool:
        answers = sorted(pool.map(work, cases), key=lambda a: a["id"])

    out.write_text(json.dumps(answers, indent=1))
    print(f"wrote {len(answers)} answers to {out}")
    return 0


def score(answers_path: Path, cases_path: Path | None = None) -> int:
    cases = {c["id"]: c for c in load_cases(cases_path)}
    raw = answers_path.read_text()
    m = re.search(r"\[.*\]", raw, re.S)
    if not m:
        sys.exit(f"{answers_path}: no JSON array found")
    answers = json.loads(m.group(0))

    hits = 0
    misses = []
    for a in answers:
        case = cases.get(a["id"])
        if not case:
            continue
        if a["choice"] == case["expected"]:
            hits += 1
        else:
            misses.append((case["prompt"], case["expected"], a["choice"], a.get("runner_up", "")))

    total = len(answers)
    print(f"routing accuracy: {hits}/{total} = {hits / total:.0%}\n")
    if misses:
        print("misses (prompt | expected | chosen | runner-up):")
        for p, e, c, r in misses:
            print(f"  {p[:52]:52s} | {e:22s} | {c:22s} | {r}")

    by_cluster: dict[str, list[int]] = {}
    for a in answers:
        case = cases.get(a["id"])
        if case:
            by_cluster.setdefault(case["cluster"], []).append(int(a["choice"] == case["expected"]))
    print("\nby cluster:")
    for cl, vals in sorted(by_cluster.items()):
        print(f"  {cl:10s} {sum(vals)}/{len(vals)}")
    return 0 if hits == total else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["build", "run", "score"])
    ap.add_argument("--answers", type=Path, help="judge output file (score mode) / output path (run mode)")
    ap.add_argument("--cases", type=Path, help="case file (default cases.jsonl)")
    ap.add_argument("--model", default="gemini-3.6-flash", help="judge model for run mode")
    args = ap.parse_args()

    if args.mode == "build":
        print(build(args.cases))
    elif args.mode == "run":
        if not args.answers:
            sys.exit("run mode needs --answers <output file>")
        sys.exit(run_per_case(args.cases, args.model, args.answers))
    else:
        if not args.answers:
            sys.exit("score mode needs --answers <file>")
        sys.exit(score(args.answers, args.cases))
