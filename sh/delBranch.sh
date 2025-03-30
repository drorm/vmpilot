#!/bin/bash

# The name of the branch to be deleted
BRANCH=$1

# Check if the branch name is one of the protected branches
if [ "$BRANCH" == "main" ] || [ "$BRANCH" == "qa" ] || [ "$BRANCH" == "gh-pages" ] || [ "$BRANCH" == "dev" ] ; then
    echo "Error: Attempting to delete a protected branch ($BRANCH). Operation aborted."
    exit 1
fi

# Confirm deletion
read -p "Are you sure you want to delete branch \"$BRANCH\" ? [y/N] " confirm_del
if [[ ! $confirm_del =~ ^[Yy]$ ]]; then
    echo "Delete aborted by user."
    exit 0
fi

# Create a tag for archival purposes with a timestamp
TAG_NAME="archive/${BRANCH}-$(date +%Y%m%d%H%M%S)"
echo "Creating tag $TAG_NAME for branch $BRANCH"
git tag $TAG_NAME $BRANCH
git push origin $TAG_NAME

# Delete the remote branch
echo "Deleting remote branch $BRANCH"
git push origin --delete $BRANCH

# Delete the local branch
echo "Deleting local branch $BRANCH"
git branch -D $BRANCH

# List remaining branches as a confirmation
git branch -a
