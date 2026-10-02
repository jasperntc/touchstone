# Third-party notices

This repository's own code and documentation are released under the MIT
licence in [LICENSE](LICENSE). The material listed here is not, and keeps its
own licence.

## anthropics/claude-plugins-official

- **Repository:** <https://github.com/anthropics/claude-plugins-official>
- **Licence:** Apache License 2.0. A copy is in
  [LICENSES/Apache-2.0.txt](LICENSES/Apache-2.0.txt), taken unmodified from the
  repository's root `LICENSE` at the commit below. The `discord`, `imessage`
  and `telegram` plugins' own `LICENSE` files carry the notice
  "Copyright 2026 Anthropic, PBC".
- **NOTICE:** at that commit there is no `NOTICE` file at the repository root
  or in any plugin that the entries below come from.
- **Redacted:** the `claude-security` entry's description, whose plugin
  licence doesn't permit redistribution, is omitted in HEAD but remains in
  history; see [errata E5](docs/errata.md).
- **What is included:** the `description` field of 30 entries in
  `eval/evidence/catalogue.json`. `tools/catalogue.py --publish` read it from
  the frontmatter of each skill's `SKILL.md` in a locally installed copy of the
  marketplace.
- **Source commit:** the installed copy recorded no commit, so the exact one
  can't be recovered. `catalogue.json` was generated on 2026-08-22, in commit
  `9c80c08` here. Every upstream `main` commit from
  `1e96c6b0a0f0` (2026-08-12) to
  `340e33aef211d95769d252324854497af871dafe` (2026-08-21) reproduces these
  entries exactly. The later one is the last upstream commit before generation
  and is the most likely source.

### Changes made to the copied text

`tools/catalogue.py` reads frontmatter with a small line parser rather than a
YAML library, and caps each description at 400 characters
(`tools/catalogue.py:70-84`, `:138`). Compared with upstream at `340e33aef211`:

- 12 descriptions are unchanged.
- 11 are truncated to 400 characters.
- 6 have the skill's `allowed-tools` list appended, e.g. ` - Read - Write - Bash(ls *)`.
- 1 keeps the opening quotation mark, has its line breaks joined, and is
  truncated to 400 characters.

| Plugin | Skill | Change |
|---|---|---|
| `external_plugins/discord` | `access`, `configure` | `allowed-tools` appended |
| `external_plugins/imessage` | `access`, `configure` | `allowed-tools` appended |
| `external_plugins/telegram` | `access`, `configure` | `allowed-tools` appended |
| `plugins/claude-code-setup` | `claude-automation-recommender` | unchanged |
| `plugins/claude-md-management` | `claude-md-improver` | unchanged |
| `plugins/cwc-makers` | `m5-onboard` | unchanged |
| `plugins/cwc-makers` | `cardputer-buddy` | truncated |
| `plugins/example-plugin` | `example-command`, `example-skill` | unchanged |
| `plugins/frontend-design` | `frontend-design` | unchanged |
| `plugins/hookify` | `writing-hookify-rules` | unchanged |
| `plugins/math-olympiad` | `math-olympiad` | opening quote kept, lines joined, truncated |
| `plugins/mcp-server-dev` | `build-mcp-app`, `build-mcp-server`, `build-mcpb` | truncated |
| `plugins/playground` | `playground` | unchanged |
| `plugins/plugin-dev` | `agent-development`, `skill-development` | unchanged |
| `plugins/plugin-dev` | `command-development`, `hook-development`, `mcp-integration`, `plugin-settings`, `plugin-structure` | truncated |
| `plugins/project-artifact` | `project-artifact` | truncated |
| `plugins/receipts` | `receipts` | truncated |
| `plugins/session-report` | `session-report` | unchanged |
| `plugins/skill-creator` | `skill-creator` | unchanged |

`eval/harness/to_benchmark.py` emits skill-creator's `benchmark.json` field
names, and `tests/test_prereg.py` checks that they still exist upstream. CI
reads skill-creator's schema from the upstream repository at a pinned commit and
does not copy it here.

## agency-agents

- **Repository:** <https://github.com/msitarzewski/agency-agents>
- **Owner:** [msitarzewski](https://github.com/msitarzewski)
- **Licence:** MIT
- **No upstream content is included in this repository.** The README's
  "predecessor" is a fork, `jasperntc/agency-agents`, which evaluated
  agency-agents' agent files. The harness here was ported from that fork's own
  `eval/` code, which is not part of upstream.
