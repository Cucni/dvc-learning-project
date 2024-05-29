# Notes

## Introduction

DVC (Data Version Control) is a tool that helps with many aspects of MLOps. While initially born specifically for tracking data, it now offers capabilities in these areas:

* Data versioning
* Experiment tracking and reproducibility
* Model registry
* Data registry

## Data versioning

Tracking data means that we have some way to version control our data. This basically mean that we want "git for data". Git is not the right tool for this job because it is made to track small files (such as code), while in machine learning datasets tend to be quite large.

Data changes over time: it gets updated or corrected, it gets expanded (new measurements, new features), it gets processed differently. We want to be able to track these changes. Things that we would like to achieve:

* reference past (or generally other) versions of the data precisely
* obtain a dataset once its reference is known
* data lineage, i.e. understand how some data was generated and review the steps that generated that particular version of a dataset
    
these would help for example when collaborating on data science projects, reproducing experiments, comparing results and pipelines, and so on. 

As noted, Git is not up to this job: while it provides most of these functionalities it does not work well on large files. The next idea is then to store our data in appropriate data storages (such as cloud storages), and put under version control with Git some identifier for the data. A basic approach is to store qualities that identify datasets, such as the number of rows and columns, the data types, etc. However, this would be dataset-specific and risks not being unique.

DVC uses this idea in a more general sense: data is stored in a "remote location", and under version control it stores a _footprint_ of the dataset, which is computed automatically. This is a hash computed on the dataset, which uniquely identifies it, and is small in size in order to play well with Git. DVC then maintains a lookup table, where the hash acts as the "index" of the hashed dataset, such that the user can simply request the dataset by its hash (the hash becomes a pointer to the dataset).

### Workflow

To track a dataset, we target it with the command `dvc add <path/to/dataset>`. This adds the dataset to a `.gitignore`, and creates a file `<path/to/dataset>.dvc` which is the footprint of the dataset. It contains a `md5` hash of the dataset and other metadata. The `<path/to/dataset>.dvc` file must then be added to version control with git, because it will be tracked this way.

The actual dataset is then stored in a cache, which is a folder in the local clone of the repo. This is not under version control. Every time the dataset changes and is added to tracking with `dvc add`, the `.dvc` file is updated (and should be committed to git), and a new copy of the dataset is made in the cache.

To obtain a different copy of the dataset, travel to another git commit with the standard `git checkout <hash>` and run `dvc checkout` (where `<hash>` is the commit hash in the git log). This will fetch from the cache the version of the dataset corresponding to the hash written in the `.dvc` file. If that version of the dataset is not in the cache, the command will give an error.

The data and the cache can be pushed and pulled to/from a remote location, which can be a cloud storage or a local filesystem. Remotes are managed with `dvc remote`. When we checkout a commit that references a different version of a dataset (via the hash), and we run `dvc checkout`, DVC tries to pull that version from the cache, but it is not guaranteed to be there. In this case, we can fetch the desired dataset version from the remote with a `dvc pull`. This pull/push mechanism allows us to avoid storing all the data versions locally: the full dataset is pulled from the remote to the cache when it is needed.

The command `dvc pull` obtains data from a remote, and populates the cache. The data it obtains is the one pointed at by the hashes in the `<path/to/dataset>.dvc"` files currently present in the folder (which means that it obtains a version of the data that is in sync with the git commit that we are on). By default, this is also the only version of the data it copies to the cache. Therefore, if we move to another commit then `dvc checkout` will not find the new data version in the cache: it is then necessary to run `dvc pull` again, which both populates the cache and checks out the data. In theory one can populate the cache with all the versions of the data by running `dvc pull -A`, but this may create a very large cache.

Remark: if we are interested in checking out a version of the data from another commit but want to keep the version of the _code_ from the current commit, then it is useful to use `git checkout <commit-hash> -- <path/to/dataset>.dvc` to obtain the hashes of the dataset only.

Summary:
* data is not stored in the git repository
* but dvc creates a ".dvc" file which is stored in the git repository
* the ".dvc" file is contains an identifier for a _version_ of the data so that we can recover that version if needed
* the .dvc file establishes a connection to the data (and its versions), but the actual data is not tracked
* data is generally stored in a remote storage, which makes up a dvc repository
* we can push/pull to the remote storage: pushing moves data to the remote storage, pull obtains data from there. DVC helps with these operations by managing a local cache.

Remark: a DVC remote acts as a Git remote (such as GitHub) for cached data.

They serve the purpose of:
* centralize data storage, helping sharing and collaboration
* synchronize files
* back up data (and other files) to avoid storing it locally


## ML Pipelines

### Prerequisites

DVC also has capabilities for managing machine learning pipelines. For the sake of this project, we will implement a simple pipeline that trains a classification model on the penguins dataset. The [Palmer penguin dataset](https://allisonhorst.github.io/palmerpenguins/) is a dataset with data about penguins (body features, location, sex) often used in data exploration and visualization and ML examples. In our case, we will use the penguins dataset to train a K-Nearest Neighbors classifier to predict the sex of a penguin given the other information at our disposal.

To implement the ML pipeline in a way that can be managed with DVC, we follow these steps:
* Obtain the dataset and put it under data version control with `dvc add` (and committing).
* Write separate scripts for processing the data, creating new features, training the model and evaluating the model.
* Refactor the pipeline such that it is parametrized according to a `params.yaml` file which contains the parameters that control the pipeline execution: data paths, model paths, parameters for data processing and feature creation, model hyperparameters, etc. Note that the `params.yaml` file is versioned with git.

This provides the basic structure that will enable us to use DVC's functionalities to manage the pipeline.

A good example of an implementation that follows can be found in the [official DVC example](https://github.com/iterative/example-get-started). Note how it touches on these points:
* structure of the file `params.yaml` and how it is accessed in the pipeline
* separation of the pipeline in the 4 separate steps
* control of pipeline parameters and execution using the parameters externalized in `params.yaml`
* reproduction of the processing steps executed in the training dataset also on the test dataset by using already fitted transformers
* persistence of processed data and serialized models

A shorter and simpler example can be found in the [project repo](https://github.com/AntonisCSt/POW_DVC/tree/main) used as reference during the DataTalks.Club activity, although this example does not address all points above equally well.

### DVC Pipelines

As said, DVC has capatibilities for managing pipelines. More precisely, it can acts as a sort of "make" for machine learning: it can identify pipeline inputs and outputs, run them automatically and sequentially, compare versions of dependencies and outputs in order to run only what needed, cache and compare results in order to avoid repeating the same processes twice, and "freeze" a snapshot of the whole pipeline. The benefits of these feature rely on a higher pipeline reproducibility and automation.

Pipelines are treated as a set of _stages_. Stages are defined by the user, but in general a good mental framework is to split a pipeline into four "main" stages: data processing, feature creation, model training and model evaluation. Of course according to the use case we can have more or less stages, some of these can be repeated multiple times (for example if we are training two models), etc. However this 4-stages-framework can be easily use to understand how DVC works.

A stage is composed of:
* a command to run
* dependencies: inputs and other files that the stage depends on. This generally includes data as input, but we can also have a serialized model as dependency. Typically one includes the source code of the command as a dependency too, see later for the motivation.
* outputs: this is what the stage creates, and of course it can go from no outputs (e.g. we evaluate the model and print the accuracy) to multiple outputs.
* parameters: these control the execution of the stage and are generally obtained from the file `params.yaml`.

Stages are created via the command `dvc stage add -n <name> -d <dependency> -o <output> -p <parameter> <command>`. Their definition is then saved into the file `dvc.yaml`, which can also be edited manually. This file should be versioned with git!

Stages are run to generate their outputs. When we ask DVC to run a stage, it will check all its dependencies: if the stage was already ran and no dependency or parameter has changed, then it will be skipped because it will produce the same output and we already have that. If any dependency or parameter has changed, then the stage will be run and the outputs overwritten. In this way DVC can make sure to only run stages when it is necessary. Remark: this is why we include the source code as a dependency, because if _that_ changes then we surely want to run the stage! Otherwise, we may risk that we change the stage implementation, but no input or parameter has changed so DVC think that the stage can be skipped.

To chain stages together in pipelines, we simply use the output of Stage 1 as a dependency of Stage 2. DVC then automatically recognizes that Stage 2 depends on Stage 1, hence when we ask to run the entire pipeline it will first run Stage 1 and after that it will run Stage 2. It will also smartly manage their dependencies and outputs to only run what is needed:
* if a dependency of Stage 1 has changed, then everything will be run again
* if a dependency of Stage 2 has changed, but no dependency of Stage 1 has changed, then we can skip Stage 1 and use its already computed output to feed Stage 2, which needs to be run again

Pipelines need not be linear, but they are viewed as graphs. They are implemented as DAG, i.e. direct acyclic graphs. As long as the definition of a DAG is met, then it is a valid pipeline.

Pipelines are run with the command `dvc repro`. Their definition as graphs of stages can be viewed in `dvc.yaml`, and graphically can be generated with `dvc dag`.

DVC understands if dependencies and outputs have changed via a "lockfile for executions", `dvc.lock`, which captures the results of the execution/reproduction. Whenever the pipeline is run with `dvc repro`, the file `dvc.lock` is written (or updated) with the hashes of all the dependencies, parameters and outputs of the pipeline. It then becomes easy for DVC to understand if something has changed by comparing the hashes. The file `dvc.lock` is then specific of a single reproduction, and it is good practice to version it with git, so that the state of the pipeline can be tracked. Remark: the `dvc.lock` file effectively tracks all the dependencies, outputs and parameters of pipeline stages by storing their hashes and keeping copies in the cache (see next itme), even when these are not explicitly added to tracking using `dvc add`.

DVC also keeps a cache of executions, so that if some dependency is reverted back to a previous version after a change, the results of the execution with `dvc repro` can be pulled from the cache, saving even more executions.

All of this affords the following:
* a pipeline can be reproduced with a single command (`dvc repro`) that runs the various stages in the correct order
* when running a pipeline, only the necessary stages are run, to avoid unnecessary reruns
* the state of a pipeline (dependencies, outputs, parameters) is captured in `dvc.lock` so that it can be easily verified and version tracked
* the definition of the stages and the snapshot of their results via the files `dvc.yaml` and `dvc.lock` makes a pipeline reproducible, since we have execution instructions, and a reference to compare the entire state to
* the specification of the stages and their details in `dvc.yaml` makes it easy to collaborate, as there is a clear and shared agreement on how to run it


## More on DVC remotes

The main feature of DVC is to efficiently coordinate remote storage for data with version control in git, so it is naturally equipped with many features that make the life easier.

* It is possible to use DVC as an interface to obtain data from a "DVC data registry", regardless of the protocol. This is done with `dvc get`. This works well as an abstraction layer, so that you can simply use the dvc CLI instead of `wget`, `curl`, proprietary tools, GUIs, etc.
* It is possible to add "private" remotes, i.e. remotes whose configuration is not put under version control with git but lives solely on our local machine. This is done by using the flag `--local` to the various commands, such as `dvc remote add --local <name> <url>`. In this case "local" does not mean that the remote is locally stored, but that it is configured exclusively on the local machine. The use case for this is when we do not want to share the configuration of the remote (or its authentication methods).
* DVC can track files from the web, and can automatically determine whether they have changed and it then necessary to download them again. This is achieved with the command `dvc import-url`. After adding a file in this way, DVC will be able to check if it has changed by checking the result with a simple HTTP request (without downloading the file).
* It is possible to track a file in a remote storage without ever downloading it. This is done with the commands `dvc import-url --no-download` and `dvc import-url --to-remote`. The use case for this is when the dataset is exceedingly large (and larger than the local machine could handle with ease) but we are still interested in tracking it. For example, this dataset could be part of our model training pipeline, which however happens entirely in cloud resources.
* Some remote storages have built-in versioning, for example AWS S3 and Azure Blobs provide this feature. In these cases, it is possible to instruct DVC to rely on the versioning mechanism of the remote storage. This is achieved with the command `dvc import-url --version-aware`. This makes it possible to track the data versioning in the git repo, but without having to download the data or add another versioning layer.


Note that the functionalities of `import-url` have two applications: one is to work with remotes, the other is to manage "external data dependencies", which means files from external locations that we want to track in the repository. While the pull mechanism may be similar for the two use cases, we never push to external data dependencies that are not remote storages.

## Tracking Metrics, plots and parameters of ML Pipelines

After data versioning and pipeline management, a third functionality that DVC provides is the ability to log metrics, plots, parameters and other outputs of model evaluations, and to compare these between different executions.

The library used for this is DVC Live (note: DVC Live is a helper library, but is not necessary to achieve this goal, see important remark below). DVC Live provides functions to log metrics, plots and parameters to call in the python scripts in order to capture the desired outputs. The outputs are logged and stored in local folders, and it is then possibe to retrieve this information with the DVC CLI.

To do proper tracking, you write an evaluation script, in which you instantiate a DVC Live context manager and inside that run model evaluation and log metrics, plots and parameters. Then for each execution, these quantities will be logged. Note that dvclive has helper modules for the most common ML frameworks, for example it has a log_sklearn_plot with which you can directly create and log the "metrics plot" that sklearn ships with (confusion matrix, ROC-AUC curve, precision-recall curve, etc.). You can also log plots that you create otherwise.

DVC Live saves the metrics and plots in a specific folder (that we generally want to gitignore). These outputs will be logged when you execute the script from command line directly. However, it is wise to add the evaluation script to your DVC pipeline by adding it as a stage. In this case its outputs (metrics and plots) will be tracked by hash in dvc.lock similarly to any other output. DVC Live also takes care of adding the necessary sections in the `dvc.yaml` file to configure DVC to track metrics and plots correctly.

When a tracked evaluation stage is reproduced, we can consult metrics and plots with the commands `dvc metrics` and `dvc plots` (and checking the HTML file this produces). If we desire to change the model parameters (or any other dependency) we will be interested in understanding how the model metrics and plots change. We can do this by reproducing the pipeline, which computes all the outputs including metrics and plots, and then checking how the newly computed metrics and plots differ from those evaluated at HEAD (the last commit) with `dvc metrics diff` and `dvc plots diff` (and then checking the HTML file with the comparison that this last command produces). In this way we can compare whether the changes have improved the model metrics and plots.

Note that metrics and plots are tracked by hash in `dvc.lock`, but this does not mean that their values (or rather, the files containing their values) are tracked! Indeed, we did not add them with `dvc add`. This is entirely analogous to how we track other outputs via `dvc.lock`: DVC can detect if the outputs/metrics/plots match thanks to the hash, but that does not add them to the "data" to be version controlled and pushed to remotes.

For this reason, in general we would expect that to reconstruct the values of metrics/plots from a previous execution, we would have to reproduce the evaluation stage, with the `dvc.lock` only telling us if there is a mismatch. However, remember that DVC maintains a cache of "recent" executions, and it does so also for logged metrics and plots (analogously to what happens for other outputs, but likely with different policies/heuristics): it is then able to pull the actual metrics/plots originating from running the pipeline at the state it was in at HEAD without re-running it. The cache allows us to revisit past metrics/plots easily.

The same workflow can be used to compare metrics and plots for any two git revisions (commits, tags, branches, etc.) as long as there was a tracked execution at those revisions. For example we can run `dvc metrics diff HEAD^ HEAD^^` to compare the metrics between the two previous commits. By default the commands compute the difference between the workspace and HEAD. Similarly, `dvc params diff` is used for inspecting and comparing params between workspace and git revisions.

Note that tracking of metrics and plots is still configured in the file `dvc.yaml`. The (independent! See comment below) sections `metrics` and `plots` contain the paths to the metrics and plots that we want to track. Committing these changes to the git repo makes sure that we are sharing our tracking configuration also for metrics and plots, and that we are storing changes for what we want to track at different stages of our ML development.

Remark: the capability of tracking metrics and plots while at the same time managing the pipeline executions (and tracking data versioning) naturally leads to the argument of "experiments" in DVC, which packages everything together. See the relevant section to know more.

### Workflow

* implement an evaluation script in which a model is evaluated by computing metrics, producing plots and potentially other outputs
* use the package dvclive to log metrics, plots and other outputs.
* add the tracked evaluation stage to the DVC pipeline with `dvc stage add ...`
* reproduce the pipeline with `dvc repro`
* commit the updated configuration file `dvc.yaml` (with the config for the additional pipeline stage and the metrics and plots) and the execution snapshot in `dvc.lock`
* consult metrics and plots using both the CLI and the generated HTML file with the commands `dvc metrics` and `dvc plots`

The enabled tracking makes it possible to compare metrics/plots/parameters between different states of the pipeline. Two common workflows are:
1. modifying parameters, source code, data or other dependencies in the current working area. After running `dvc repro`, it is possible not only to consult the current outputs (following the above workflow) but also to compare their value between the current workspace and the another git revision (by default the last commit -- HEAD) with `dvc metrics diff <git-revision>` and `dvc plots diff <git-revision>`.
1. compare the outputs between two arbitrary git revisions of the repo with `dvc metrics diff <git-revision-1> <git-revision-2>` and `dvc plots diff <git-revision-1> <git-revision-2>`.

These workflow scenarios help to understand the effect of changes to a pipeline

Note that differently from mlflow, dvclive does not provide functionalities for logging models and other artifacts or for managing a model registry

**Important remark**

The above is _one way_ to track metrics and plots, but it is not the only way. The above way uses DVC Live and its helpers log_metrics and so on, to track "live" metrics, plots, etc. Using the DVC Live helpers makes DVC automatically recognize that a particular script (say `evaluate.py`) will output some metrics, some plots and possibly other stuff. Knowing this, DVC creates the `metrics` and `plots` sections in `dvc.yaml` to configure itself in order to track them. Note that the sections `metrics` and `plots` are NOT part of a pipeline stage, they are their own independent sections, even though the metrics/plots originated from a pipeline stage.

A similar result can be obtained by having "more manual" logging in the script, for example by simply printing metrics and saving plots to a file _without_ the DVC Live helpers. When adding the stage to the pipeline we then need to explicitly instruct DVC that the stage will produce some metrics and plots. This is done with the options `dvc stage add -m <metrics_path> --plots <plot_path>` that will instruct DVC accordingly (there are options also for adding them with cache disabled). Note that in this case too, the sections `metrics` and `plots` of the file `dvc.yaml` are independent, not part of a pipeline stage even though we added these metrics and plots while adding a stage.

A third option of course is to manually populate the file `dvc.yaml` with the paths to the metrics and plots that we want to track.

Knowing this, it becomes clear that logging by using the DVC Live helpers triggers some automation when it comes to configuring the tracking of metrics and plots, but it is not intrinsically different than doing it manually or via `dvc stage add`, and using DVC Live is not strictly necessary.

**Reports**

One quick way to produce a summary of all the metrics/plots being tracked is with reports. It is possible to produce reports automatically using the dvclive helper `make_report`, but if using the context manager this will be triggered automatically upon context exit (but you need to specify the desired format for it to be produced). Reports can be generated in three formats: HTML, markdown or directly into notebooks. Reports are saved to the same folder where dvclive saves all other outputs, therefore generally gitignored, but the entire folder is tracked via `dvc.lock` as said above. There are CLI commands to consult them (they can be opened directly) or compare them across revisions.

## Experiments

An experiment is the set of trackable changes associated with the execution of a pipeline. This includes code and dependency changes and resulting artifacts like plots, charts and models. Running an experiment means to execute a DVC pipeline, to store and track its outputs and states, and to make them available for later inspection and comparison.

Once we have a pipeline with implemented tracking of metrics/plots, we can run it in two ways: `dvc repro` or `dvc exp run`. The first reproduces the pipeline as explained above. The second saves the results as an experiment. This means that it links together all its pieces (data, code, params, outputs, metrics, plots) and stores their states in a log, in addition to performing the usual pipeline execution with the creation of an updated `dvc.lock`. In this way we are actually creating a new experiment from the existing pipeline, and logging one experiment run. In essence, `dvc exp run` is an experiment-specific version of `dvc repro` that in addition to running the pipeline makes it outputs accessible to the experiment tooling as described below. Of course not all pipelines need to end up in experiments: for example for pure ETL pipelines it makes sense to not have them as experiments, but just run them with `dvc repro`.

Experiments are de-facto versions of ML projects, and as said they can include all the pieces of a data pipeline (and the associated objects) that can be tracked: data, code, metrics, plots, etc. They appear similarly to git commits, and indeed they are implemented as git refs that are moved around, but they are invisible to git. Whenever we do the command `dvc exp run` we create and log a new run of the experiment, using the dependencies, code and parameters present in the workspace. The results of this experiment run become accessible in the workspace and can be consulted with experiment-speficic CLI (`dvc exp`) and also with the CLI seen above for metrics/plots.

The experiment run results are also saved to an experiment log with a random name (but can be named explicitly if we want). This log of experiment runs can then be consulted to see for each experiment the state of its dependencies, params, code, outputs and metrics: some of these can be consulted with their actual values (params and metrics), while the others are reported with the hashes. This allows for easy comparison of experiments' results.

Note that the above has a similar workflow to mlflow.

Experiments can be managed with useful tooling, which allows for example to execute a run with a prescribed set of parameters, or to bring the pipeline into the state of previous experiment run. All of these operations are meant to facilitate experimentation and comparison. However, as said before experiments are not tracked in git, which means that they will not appear in the git history. To persist an experiment in git, we can use the standard git commands to add the updated version of code, params and config files and commit them. This will make the experiment accessible in the git history, it will be permanent. Note that DVC-tracked data and artifacts will not end up there because they are tracked with DVC.

Experiments provide commands that facilitate managing everything together, but we can also use the already existing tools:
* list the existing experiments with `dvc exp list`
* show the existing experiments (inclusive of parameters, metrics and hashes for dependencies and outputs) with `dvc exp show`
* compare experiments with `dvc exp diff`
* consult metrics/plots with `dvc metrics` and `dvc plots`
* compare metrics/plots with `dvc metrics diff` and `dvc plots diff`
* run an experiment with an on-the-fly update to a parameter with `dvc exp run --set-param <param-name>=<param-value>`

As said experiments are similar to git commits, in this sense it is possible to "checkout" another experiment. The workflow is as follows: say for example that we see from `dvc exp show` that a given experiment has better metrics than the experiment currently in the workspace (this basically means that a previous "commit" has better metrics than the workspace situation; in this context "experiment" translates to the "experiment run" of mlflow jargon). Then we can obtain that experiment with `dvc exp apply <exp-name>`. This will change the current workspace so that the versions of code, dependencies and outputs match those of experiment `<exp-name>`: note that this means that the code is checked out from the associated git commit, data is checked out from the DVC version control, and outputs/metrics are checked out from the DVC cache. This is because experiments are exactly meant to wrap these pieces together into a unified interface.