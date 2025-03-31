#!/bin/bash

# Check if a branch name is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <branch-name>"
    exit 1
fi

BRANCH_NAME=$1
DEV_BRANCH="dev"

# Step 1: Switch to the specified branch
echo "Switching to branch: $BRANCH_NAME..."
git checkout $BRANCH_NAME
if [ $? -ne 0 ]; then
    echo "Error: Failed to switch to branch $BRANCH_NAME."
    exit 1
fi

# Reports will be saved to the existing reports directory
echo "Reports directory: $(pwd)/reports"

# Step 3: Run linting checks, tests, type checking, and coverage
echo "Running tests and quality checks..."
cd tests
python3 -m pytest unit
./e2e_tests.sh
cd /home/dror/vmpilot/sh && ./lint.sh
cd /home/dror/vmpilot

# Run type checking
echo "Running type checking..."
./tests/sh/type_check.sh || true

# Run coverage analysis
echo "Running coverage analysis..."
./tests/sh/coverage.sh || true

# Inform the user
echo "Check the reports directory for type checking and coverage results"

# Step 3: Switch to dev branch
echo "Switching to $DEV_BRANCH branch..."
git checkout $DEV_BRANCH
if [ $? -ne 0 ]; then
    echo "Error: Failed to switch to $DEV_BRANCH branch."
    exit 1
fi

# Step 4: Check for changes in dev compared to the feature branch
#echo "Checking if $DEV_BRANCH has diverged from $BRANCH_NAME..."
#if ! git merge-base --is-ancestor $BRANCH_NAME $DEV_BRANCH; then
    #echo "Error: $DEV_BRANCH is ahead or has changes compared to $BRANCH_NAME. Aborting merge."
    #exit 1
#fi

# Step 5: Run git diff
echo "Displaying changes between $DEV_BRANCH and $BRANCH_NAME..."
git diff $DEV_BRANCH $BRANCH_NAME

# Show status
git status

# Step 6: Confirm merge
read -p "Are you sure you want to merge $BRANCH_NAME into $DEV_BRANCH? [y/N] " confirm_merge
if [[ ! $confirm_merge =~ ^[Yy]$ ]]; then
    echo "Merge aborted by user."
    exit 0
fi

# Step 7: Merge the branch into dev
echo "Merging $BRANCH_NAME into $DEV_BRANCH..."
git merge --ff-only $BRANCH_NAME
if [ $? -ne 0 ]; then
    echo "Error: Merge conflict or issue detected. Please resolve manually."
    exit 1
    # else commit the changes
else
    echo "Merge successful. Please review the changes and commit them."
    # commit the changes
    git commit
fi

echo "👍✅ Merge completed successfully. Please review the changes and push them if everything is correct.👍✅ "
