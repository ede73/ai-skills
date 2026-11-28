# AI Skills

Reusable agent skills live in `skills/`. Shared executable programs used by one or more skills live in `programs/`.

## Make the skills available to Codex

After cloning this repository, run:

```sh
./scripts/link-codex-global-skills.sh
```

This creates `~/.agents/skills/ai-skills` as a symlink to this clone's `skills/` folder. Codex discovers skills nested under that link, including skills added to the repository later.

The script leaves the rest of `~/.agents/skills` and `~/.codex/skills` alone. Skills you create beside the `ai-skills` link stay local; only folders inside this repository's `skills/` folder are shared through the link.
