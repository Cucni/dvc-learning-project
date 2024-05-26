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

## More on DVC remotes

The main feature of DVC is to efficiently coordinate remote storage for data with version control in git, so it is naturally equipped with many features that make the life easier.

* It is possible to use DVC as an interface to obtain data from a "DVC data registry", regardless of the protocol. This is done with `dvc get`. This works well as an abstraction layer, so that you can simply use the dvc CLI instead of `wget`, `curl`, proprietary tools, GUIs, etc.
* It is possible to add "private" remotes, i.e. remotes whose configuration is not put under version control with git but lives solely on our local machine. This is done by using the flag `--local` to the various commands, such as `dvc remote add --local <name> <url>`. In this case "local" does not mean that the remote is locally stored, but that it is configured exclusively on the local machine. The use case for this is when we do not want to share the configuration of the remote (or its authentication methods).
* DVC can track files from the web, and can automatically determine whether they have changed and it then necessary to download them again. This is achieved with the command `dvc import-url`. After adding a file in this way, DVC will be able to check if it has changed by checking the result with a simple HTTP request (without downloading the file).
* It is possible to track a file in a remote storage without ever downloading it. This is done with the commands `dvc import-url --no-download` and `dvc import-url --to-remote`. The use case for this is when the dataset is exceedingly large (and larger than the local machine could handle with ease) but we are still interested in tracking it. For example, this dataset could be part of our model training pipeline, which however happens entirely in cloud resources.
* Some remote storages have built-in versioning, for example AWS S3 and Azure Blobs provide this feature. In these cases, it is possible to instruct DVC to rely on the versioning mechanism of the remote storage. This is achieved with the command `dvc import-url --version-aware`. This makes it possible to track the data versioning in the git repo, but without having to download the data or add another versioning layer.


Note that the functionalities of `import-url` have two applications: one is to work with remotes, the other is to manage "external data dependencies", which means files from external locations that we want to track in the repository. While the pull mechanism may be similar for the two use cases, we never push to external data dependencies that are not remote storages.