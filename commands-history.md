**Day 1**
```
# Initialize repo and commit
dvc init
git commit

# Track toy dataset
dvc add data/toy-data.txt
git st
git add data/toy-data.txt.dvc data/.gitignore
git commit

# Check status to see file has changed, add new version
(toy dataset edited)
dvc status
dvc diff
dvc add data/toy-data.txt
git st
git diff
git add data/toy-data.txt.dvc
git commit

# Checkout past commit, and use DVC to checkout relevant version of dataset
git log -3
git ch 125e367
dvc status
dvc checkout

# Return to main branch, checkout relevant version of dataset
git ch main
dvc checkout

# Add a remote storage named "local" that points to the folder "/tmp/dvcremote". The option "-d" makes it the default remote. Then push the cache to that remote. This adds some config so we add it to git.
dvc remote add -d local /tmp/dvcremote
dvc push -r local
git add .dvc/config
git commit
```