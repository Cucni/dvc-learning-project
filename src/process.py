from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

DATA_FOLDER = Path("data/")


def main(data_folder: Path, dest_folder: Path) -> None:
    # Load data
    dataset = pd.read_csv(data_folder / "penguins.csv")

    # Clean data: drop unused column and records with missing values
    dataset = dataset.drop(columns=["island"]).dropna()

    # Split into train and test datasets
    dataset_train, dataset_test = train_test_split(
        dataset, train_size=0.8, shuffle=True, random_state=10
    )

    # Save cleaned datasets
    dataset_train.to_csv(dest_folder / "penguins_train.csv")
    dataset_test.to_csv(dest_folder / "penguins_test.csv")


if __name__ == "__main__":
    main(DATA_FOLDER, DATA_FOLDER / "processed")
