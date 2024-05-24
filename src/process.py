from pathlib import Path

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

DATA_FOLDER = Path("data/")
PARAMS_FILE = Path("params.yaml")


def main(data_folder: Path, dest_folder: Path) -> None:
    # Load parameters from params.yaml
    with open(PARAMS_FILE, "r") as params_file:
        params = yaml.safe_load(params_file)["process"]

    # Load data
    dataset = pd.read_csv(data_folder / "penguins.csv")

    # Clean data: drop unused column and records with missing values
    dataset = dataset.drop(columns=["island"]).dropna()

    # Split into train and test datasets
    dataset_train, dataset_test = train_test_split(
        dataset,
        train_size=params["train_size"],
        shuffle=True,
        random_state=params["random_state"],
    )

    # Save cleaned datasets
    dataset_train.to_csv(dest_folder / "penguins_train.csv")
    dataset_test.to_csv(dest_folder / "penguins_test.csv")


if __name__ == "__main__":
    main(DATA_FOLDER, DATA_FOLDER / "processed")
