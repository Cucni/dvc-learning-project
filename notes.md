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

The actual dataset is then stored in a cache, which is a folder in the local clone of the repo. This is not versioned control. Every time the dataset changes and is added to tracking with `dvc add`, the `.dvc` file is updated (and should be added to git), and a new copy of the dataset is made in the cache.

To obtain a different copy of the dataset, travel to another git commit and run `dvc checkout <hash>`. This will fetch the version of the dataset corresponding to the hash written in the `.dvc` file from the cache.

The cache can be pushed and pulled to/from a remote location, which can be a cloud storage or a local filesystem.