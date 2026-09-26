# Contribution snake

The profile README displays animated SVGs generated from the repository owner's
real GitHub contribution calendar using [Platane/snk](https://github.com/Platane/snk).
The snake uses a warm gold accent over the profile's existing moss-green palette.
Light and dark SVGs follow the viewer's color scheme.

## Update workflow

- Workflow: `.github/workflows/contribution-rhythm.yml` (Update contribution snake).
- Runs daily at 02:25 UTC / 10:25 Asia/Shanghai; GitHub may delay scheduled runs.
- Also runs when its workflow file changes on main, or via Actions → Run workflow.
- Outputs: `assets/contribution-snake-light.svg` and `assets/contribution-snake-dark.svg`.
- Generation uses a pinned Platane/snk commit and a temporary, read-only GITHUB_TOKEN.
- A separate publish job downloads the validated SVGs and commits only these two files.
  Only this job has contents-write permission; it runs no Platane action.
- No personal access token, external hosting, or custom repository secret is required.

For the initial rollout, publish the workflow first and wait for both SVGs to be
committed before switching the README, so the profile never references missing images.
The previous contribution-rhythm images and optional docs site remain as legacy assets;
this workflow refreshes the snake SVGs only.

The SVGs contain looping CSS animations. The underlying contribution snapshot refreshes
daily; individual cell details remain available through the linked GitHub calendar.
