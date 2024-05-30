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

**Day 4**
```
# Add a "process" stage in the DVC pipeline, check its specification and the dag
dvc stage add -n process -d src/process.py -d data/penguins.csv -p process.train_size,process.random_state -o data/processed/penguins_train.csv -o data/processed/penguins_test.csv python src/process.py
bat dvc.yaml
dvc dag

# Add a "featurize" and a "train" stage in the DVC pipeline, check the updated stages specifications and the updated dag. Then commit the pipeline implementation
bat params.yaml
dvc stage add -n featurize -d data/processed/penguins_train.csv -d data/processed/penguins_test.csv -o data/processed/train_processed.csv -d src/create_features.py -o data/processed/test_processed.csv -o artifacts/feature_encoder.joblib -o artifacts/label_encoder.joblib python src/create_features.py
bat dvc.yaml
dvc stage add -n train -p train.n_neighbors,train.train_dataset_name,train.test_dataset_name -d src/train.py -d data/processed/train_processed.csv -d data/processed/test_processed.csv -o artifacts/model.joblib python src/train.py
bat dvc.yaml
dvc dag
git add dvc.yaml
git commit

# Reproduce the pipeline, check the execution snapshot and commit it
dvc repro
bat dvc.lock
git add dvc.lock
git commit

# Change a parameter, check the status and reproduce the pipeline to observe what is skipped and what is not.
vim params.yaml
dvc status
dvc repro
vim params.yaml
dvc status
dvc repro

# Check if the pipeline stages are up to date (checks dependencies, outputs and parameters), without running them
dvc repro --dry
```

**Day 5**
```
# Implement tracking of live metrics/plots, run the script manually to produce them. Then check metrics and plots.
(implement dvclive tracking in the evaluate.py script)
python src/evaluate.py
dvc metrics show
dvc plots show
open dvc_plots/index.html

# Add the evaluation stage to the pipeline. Check implementation in dvc.yaml. Then reproduce the pipeline, and check the outputs.
dvc stage add -n evaluate -p evaluate.test_dataset_name -d src/evaluate.py -d artifacts/model.joblib -d data/processed/test_processed.csv -o eval python src/evaluate.py
cat dvc.yaml
dvc repro
dvc plots show
open dvc_plots/index.html
dvc metrics show
dvc params show
git add dvc.yaml dvc.lock .gitignore src/evaluate.py
git commit

# Change a parameter, then reproduce the pipeline and consult the changed metrics/plots/params. Commit the result (because satisfactory)
vim params.yaml
dvc repro
dvc metrics show
# The commands below show the changes between the workspace and the last commit (HEAD).
dvc params diff
dvc params diff --all
dvc metrics diff
dvc plots diff
open dvc_plots/index.html
git add params.yaml dvc.lock
git commit

# Consult the changes of parameters between workspace and HEAD^
dvc params diff HEAD^
# Consult the changes of parameters and metrics between HEAD and HEAD^
dvc params diff HEAD^ HEAD
dvc metrics diff HEAD^ HEAD
```

**Day 6**
```
# Implement report creation in markdown, reproduce the pipeline and consult the report
(edit the evaluation script to produce reports in markdown format)
dvc repro
open eval/report.md
git add src/evaluate.py dvc.lock
git commit

# Check that DVC can already view the existing workspace as an experiment run, but there is no recorded previous history as we always used `dvc repro`
dvc exp show
dvc exp show --only-changed
dvc exp diff

# Use exp run to run the pipeline instead of repro so that the outputs are tracked as experiment results
# This uses the version of code, params, dependencies as of HEAD
dvc exp run
dvc exp show
dvc exp show --only-changed

# Edit a parameter and launch an experiment run. Then show the experiment log to see the newly created run, and consult parameters. The param was changed in the workspace, but it wasn't committed. Nevertheless we will have a permanent reference to this execution with the edited parameter in the experiment log (but NOT in git). We can make the new state persistent by committing the workplace state.
vim params.yaml
dvc exp run
dvc exp show
dvc exp show --only-changed
dvc params diff
dvc params diff --all

# Run experiment with on-the-fly parameter change. Consult the experiment log and check that the parameter was changed in the workspace.
dvc exp run --set-param train.n_neighbors=3
dvc exp show --only-changed
dvc params diff

# Consult the experiment log, find the best run and use "apply" to make the workspace match that run. Then check the experiment log again for confirmation.
dvc exp show --only-changed
dvc exp apply sable-caps
dvc exp show --only-changed
```

**Day 7**
```
10008  dvc list .
10017  dvc list . --dvc-only
10009  dvc list https://github.com/iterative/dataset-registry get-started



10010  dvc exp list origin
(nothing as no exp has been pushed yet)

# Push the cache
10014  dvc push

# Check that experiments have not been pushed!
10032  dvc exp list origin
10033  dvc exp push
# > No experiments to push.
# This is because we are on a commit that has no associated experiments

# Show all the experiments, push an experiment by giving its name
dvc exp show -A
dvc exp push origin sable-caps
# > Pushed experiment sable-caps to Git remote 'origin'.

# Check remote experiments: this gives an empty output as on the remote we are on a commit without associated experiments
dvc exp list origin

# Finally we can see the remote experiment by listing them from all commits
# dvc exp list -A origin
d005e19:
	sable-caps

```