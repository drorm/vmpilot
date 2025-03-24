#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
MILESTONE_NUMBER=""
EDITOR="${EDITOR:-vi}"
CHANGELOG_FILE="$(git rev-parse --show-toplevel)/CHANGELOG.md"

usage() {
    echo "Usage: $0 -m MILESTONE_NUMBER [-e EDITOR]"
    echo
    echo "Options:"
    echo "  -m MILESTONE_NUMBER  Milestone number to prepare for release"
    echo "  -e EDITOR            Editor to use for release notes (default: $EDITOR)"
    echo "  -h                   Show this help message"
    exit 1
}

while getopts "m:e:h" opt; do
    case $opt in
        m) MILESTONE_NUMBER="$OPTARG" ;;
        e) EDITOR="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

if [ -z "$MILESTONE_NUMBER" ]; then
    echo -e "${RED}Error: Milestone number is required${NC}"
    usage
fi

# Function to check if command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: $1 is required but not installed.${NC}"
        exit 1
    fi
}

# Check required commands
check_command "gh"
check_command "python3"
check_command "git"

echo -e "${YELLOW}=== VMPilot Release Preparation ===${NC}"
echo -e "${YELLOW}Preparing release for milestone #$MILESTONE_NUMBER${NC}"

# Step 1: Check if we're on the dev branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "dev" ]; then
    echo -e "${RED}Error: You must be on the 'dev' branch to prepare a release.${NC}"
    echo -e "${YELLOW}Current branch: $CURRENT_BRANCH${NC}"
    exit 1
fi

# Step 2: Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}Error: You have uncommitted changes.${NC}"
    echo -e "${YELLOW}Please commit or stash your changes before preparing a release.${NC}"
    exit 1
fi

# Step 3: Pull latest changes
echo -e "${GREEN}Pulling latest changes from origin/dev...${NC}"
git pull origin dev

# Step 4: Get version from milestone
echo -e "${GREEN}Fetching milestone information...${NC}"
# First, get the milestone ID by listing all milestones and finding the one with the specified title
MILESTONE_DATA=$(gh api repos/:owner/:repo/milestones --jq '.[] | {number: .number, title: .title}')
MILESTONE_ID=$(echo "$MILESTONE_DATA" | jq -r "select(.title == \"$MILESTONE_NUMBER\") | .number")

if [ -z "$MILESTONE_ID" ]; then
    echo -e "${RED}Error: Could not find milestone with title '$MILESTONE_NUMBER'${NC}"
    exit 1
fi

echo -e "${GREEN}Found milestone ID: $MILESTONE_ID for milestone title: $MILESTONE_NUMBER${NC}"
MILESTONE_INFO=$(gh api repos/:owner/:repo/milestones/$MILESTONE_ID)
VERSION=$(echo "$MILESTONE_INFO" | grep -o '"title":"[^"]*' | cut -d '"' -f 4)
echo -e "${GREEN}Version from milestone: $VERSION${NC}"

# Step 5: Run tests
echo -e "${GREEN}Running tests...${NC}"
# Explicitly run only unit tests, excluding any experimental tests in tests/new
if ! python3 -m pytest tests/unit; then
    echo -e "${RED}Tests failed. Please fix the issues before proceeding with the release.${NC}"
    exit 1
fi
echo -e "${GREEN}All tests passed!${NC}"

# Step 5.5: Freeze dependencies
echo -e "${GREEN}Freezing dependencies...${NC}"
if ! ./sh/freeze_deps.sh; then
    echo -e "${RED}Failed to freeze dependencies. Please fix the issues before proceeding with the release.${NC}"
    exit 1
fi
echo -e "${GREEN}Dependencies frozen successfully!${NC}"

# Step 6: Generate release notes and update CHANGELOG.md
echo -e "${GREEN}Generating release notes for CHANGELOG.md...${NC}"

# Get current date in YYYY-MM-DD format
RELEASE_DATE=$(date +%Y-%m-%d)

# Get the last release tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo "No previous tag found, generating notes from all merged PRs"
    # Get all merged PRs
    NOTES=$(gh pr list --state merged --base dev --json number,title,mergedAt,author --jq '.[] | "- #\(.number): \(.title) (@\(.author.login))"' | sort)
else
    echo "Generating notes since $LAST_TAG"
    # Get PRs merged since last tag
    SINCE=$(git log -1 --format=%ai $LAST_TAG)
    NOTES=$(gh pr list --state merged --base dev --json number,title,mergedAt,author --jq '.[] | select(.mergedAt > "'"$SINCE"'") | "- #\(.number): \(.title) (@\(.author.login))"' | sort)
fi

# Also get issues from this milestone
MILESTONE_ISSUES=$(gh issue list --milestone "$MILESTONE_NUMBER" --state closed --json number,title,author --jq '.[] | "- #\(.number): \(.title) (@\(.author.login))"' | sort)

# Combine PRs and issues, remove duplicates
ALL_NOTES=$(echo -e "$NOTES\n$MILESTONE_ISSUES" | sort | uniq)

# Check for commits not associated with PRs or issues
echo -e "${GREEN}Checking for commits not associated with PRs or issues...${NC}"
echo -e "${YELLOW}Review the following commits to ensure they're represented in the changelog:${NC}"
if [ -z "$LAST_TAG" ]; then
    git log --oneline
else
    git log ${LAST_TAG}..HEAD --oneline
fi
echo -e "${YELLOW}Please ensure all significant changes above are included in the changelog.${NC}"

# Create a temporary file for the new changelog entry
TEMP_CHANGELOG_ENTRY=$(mktemp)

# Format the new changelog entry
cat > "$TEMP_CHANGELOG_ENTRY" << EOF
## [$VERSION] - $RELEASE_DATE

### Added
$ALL_NOTES

### Changed
- None

### Fixed
- None

### Breaking Changes
- None

### Known Issues
- None

EOF

# Create a temporary file for the full changelog
TEMP_FULL_CHANGELOG=$(mktemp)

# Check if CHANGELOG.md exists
if [ -f "$CHANGELOG_FILE" ]; then
    # Extract header (everything before the first version entry)
    awk 'BEGIN {p=1} /^## \[/ {p=0} p {print}' "$CHANGELOG_FILE" > "$TEMP_FULL_CHANGELOG"
    
    # Append the new entry
    cat "$TEMP_CHANGELOG_ENTRY" >> "$TEMP_FULL_CHANGELOG"
    
    # Append the rest of the existing changelog (skipping the header)
    awk 'BEGIN {p=0} /^## \[/ {p=1} p {print}' "$CHANGELOG_FILE" >> "$TEMP_FULL_CHANGELOG"
else
    # Create a new changelog file with header
    echo "# Changelog" > "$TEMP_FULL_CHANGELOG"
    echo "" >> "$TEMP_FULL_CHANGELOG"
    echo "All notable changes to this project will be documented in this file." >> "$TEMP_FULL_CHANGELOG"
    echo "" >> "$TEMP_FULL_CHANGELOG"
    
    # Append the new entry
    cat "$TEMP_CHANGELOG_ENTRY" >> "$TEMP_FULL_CHANGELOG"
fi

# Step 7: Edit changelog entry
echo -e "${GREEN}Opening changelog in $EDITOR...${NC}"
echo -e "${YELLOW}Please review and edit the changelog entry.${NC}"
$EDITOR "$TEMP_FULL_CHANGELOG"

# Move the edited changelog to the actual CHANGELOG.md file
cp "$TEMP_FULL_CHANGELOG" "$CHANGELOG_FILE"

# Clean up temporary files
rm -f "$TEMP_CHANGELOG_ENTRY" "$TEMP_FULL_CHANGELOG"

# Step 8: Confirm proceeding with release
echo
echo -e "${YELLOW}CHANGELOG.md has been updated with release notes for v$VERSION${NC}"
echo
read -p "Do you want to commit the changes and proceed with the release? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Release preparation aborted.${NC}"
    exit 0
fi

# Commit the updated CHANGELOG.md and frozen dependencies
echo -e "${GREEN}Committing updated CHANGELOG.md and frozen dependencies...${NC}"
git add "$CHANGELOG_FILE" requirements.txt requirements-dev.txt
git commit -m "Update CHANGELOG.md and freeze dependencies for release v$VERSION"
git push origin dev

# Step 9: Verify milestone is ready
OPEN_ISSUES=$(gh issue list --milestone "$MILESTONE_ID" --state open --json number | jq length)
if [ "$OPEN_ISSUES" -gt 0 ]; then
    echo -e "${RED}Warning: There are still $OPEN_ISSUES open issues in milestone #$MILESTONE_NUMBER (ID: $MILESTONE_ID).${NC}"
    read -p "Do you want to proceed anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Release preparation aborted.${NC}"
        exit 0
    fi
fi

# Step 10: Instructions for triggering release workflow
echo -e "${GREEN}Release preparation complete!${NC}"
echo
echo -e "${YELLOW}To trigger the release workflow:${NC}"
echo "1. Go to: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/workflows/release.yml"
echo "2. Click 'Run workflow'"
echo "3. Enter milestone number: $MILESTONE_NUMBER"
echo "4. Select 'Run workflow'"
echo
echo -e "${YELLOW}The release notes will be automatically extracted from CHANGELOG.md${NC}"

exit 0
