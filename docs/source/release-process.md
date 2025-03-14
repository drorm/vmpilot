# VMPilot Release Process

This document outlines the process for creating and publishing VMPilot releases.

## Branching Strategy

VMPilot follows a simplified Git Flow branching strategy:

- `main` - Production-ready code, deployed to users
- `dev` - Integration branch for development work
- Feature branches - Individual features branched from `dev`

All development work happens in feature branches, which are merged into `dev` via pull requests. When ready for release, `dev` is merged into `main`.

## Release Preparation

Before triggering the release workflow, run the local preparation script to ensure everything is ready:

```bash
./scripts/prepare-release.sh -m <milestone-number>
```

This script will:

1. Verify you're on the `dev` branch with no uncommitted changes
2. Pull the latest changes from the remote repository
3. Extract the version number from the milestone
4. Run tests to ensure everything is working
5. Generate draft release notes for review
6. Open the notes in your editor for customization
7. Check if there are any open issues in the milestone
8. Provide instructions for triggering the release workflow

## Release Workflow

The actual release is handled by a GitHub Actions workflow that:

1. Merges `dev` into `main`
2. Creates a GitHub release with version tag
3. Builds and pushes the Docker image to GitHub Container Registry
4. Closes the milestone

To trigger the release workflow:

1. Go to the [Actions tab](https://github.com/drorm/vmpilot/actions/workflows/release.yml)
2. Click "Run workflow"
3. Enter the milestone number
4. Optionally select "Create a draft release" if you want to review before publishing
5. Click "Run workflow"

## Versioning

VMPilot uses semantic versioning (MAJOR.MINOR.PATCH):

- MAJOR: Incompatible API changes
- MINOR: Backwards-compatible functionality
- PATCH: Backwards-compatible bug fixes

Version numbers are stored in milestone titles.

## Post-Release

After a successful release:

1. Verify the Docker image is available on GitHub Container Registry
2. Check that the GitHub release was created correctly
3. Ensure the milestone was closed
4. Announce the release to users

## Hotfixes

For critical issues that need immediate fixes:

1. Create a hotfix branch from `main`
2. Fix the issue and test thoroughly
3. Create a PR to merge back to both `main` and `dev`
4. Create a new patch version release