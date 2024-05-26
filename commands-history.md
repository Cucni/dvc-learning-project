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

**Day 2**
```
# Track penguin dataset
dvc add data/penguins.csv
git add data/penguins.csv.dvc data/.gitignore
git commit

# Implement pipeline and run it
(write pipeline code)
python src/process.py
python src/create_features.py
python src/train.py
python src/evaluate.py
```

**Day 3**
```
# Add a "remote" using the flag "--local" to keep it private
dvc remote add --local test /tmp/test
# Verify that no remote configuration is being noted by git because we used the flag "--local"
git st
# Print the configuration of the private remotes
cat .dvc/config.local
# Verify that .dvc/config.local is being gitignored
cat .dvc/.gitignore
# Remove the private remote
dvc remote --local remove test

# Add a remote cloud storage using google drive
dvc remote add gdrive-storage gdrive://1x5WCftJGMhGqo2hHrA46GUr7DoN_K0VI
# Make it the default remote and verify it
dvc remote default gdrive-storage
dvc remote default
# Push data to the default remote (google drive) and commit the configuration
dvc push
git add .dvc/config
git commit

# Change the dataset (artificially) by appending 10 random lines
shuf -n 10 penguins.csv >> penguins.csv
# Add the new version of the dataset to DVC tracking, then commit to git and finally push the new dataset to the remote.
dvc add data/penguins.csv
git add data/penguins.csv.dvc
git commit
dvc push

# Checkout the previous version of the dataset by travelling to a commit and running `dvc checkout`. Then travel back to the main branch and run `dvc checkout` again, to obtain the latest version of the data.
git log
git ch 948c24e
dvc status
dvc checkout
git ch main
dvc status
dvc checkout

# Remove the data and the DVC cache, pull from remote to obtain the data.
rm data/penguins.csv
rm -rf .dvc/cache
dvc pull
dvc status

# Checkout a commit with the previous version of the dataset, and try to obtain a previous version of the data with the usual `dvc checkout`.
git log
git ch 948c24e
dvc status
# dvc checkout fails because the requested file is not in the cache. When we ran `dvc pull` we only obtained (and cached) the version of the dataset corresponding to the current commit.
dvc checkout
# We can use `dvc pull -A` to obtain all versions of the data.
dvc pull -A

# Return to main and checkout the latest version of the dataset.
git ch main
dvc checkout
git log --oneline
# Checkout only the file penguins.csv.dvc (the footprint of the dataset) from a commit that used the previous version of the dataset.
git ch 1154d29 -- data/penguins.csv.dvc
# Verify that DVC is aware of the mismatch between the dataset and the hash in penguins.csv.dvc. Use checkout to obtain the version of the dataset that pointed to by the hash.
dvc status
dvc checkout
dvc status
git commit
 ```