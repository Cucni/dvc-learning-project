from pathlib import Path

import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

DATA_FOLDER = Path("data/")


def featurize_pipeline(
    df: pd.DataFrame,
    dataset_kind: str,
    feature_encoder: OneHotEncoder,
    label_encoder: LabelEncoder,
) -> pd.DataFrame:
    # Fit both encoders to the training set, else apply it already fitted
    if dataset_kind == "train":
        feature_encoder.fit(df[["species"]])
        label_encoder.fit(df["sex"])

    # One-hot encoding the categorical feature "species"
    output_df = (
        df.join(feature_encoder.transform(df[["species"]]))
        # Drop the categorical "species" just encoded
        .drop(columns=["species"])
        # Drop rows with missing values
        .dropna()
    )

    # Encode the target labels which are originally stored as categories
    output_df["sex"] = label_encoder.transform(output_df["sex"])

    return output_df


def main(data_folder: Path, dest_folder: Path, artifact_folder: Path) -> None:
    # Load datasets
    df_train = pd.read_csv(data_folder / "penguins_train.csv")
    df_test = pd.read_csv(data_folder / "penguins_test.csv")

    # Instantiate feature encoder and label encoder to use for both datasets
    feature_encoder = OneHotEncoder(sparse_output=False, dtype="int").set_output(
        transform="pandas"
    )
    label_encoder = LabelEncoder()

    # Create new features in both train and test datasets
    df_train = featurize_pipeline(df_train, "train", feature_encoder, label_encoder)
    df_test = featurize_pipeline(df_test, "test", feature_encoder, label_encoder)

    # Save datasets and encoders to disk
    df_train.to_csv(dest_folder / "train_processed.csv")
    df_test.to_csv(dest_folder / "test_processed.csv")
    joblib.dump(feature_encoder, artifact_folder / "feature_encoder.joblib")
    joblib.dump(label_encoder, artifact_folder / "label_encoder.joblib")


if __name__ == "__main__":
    main(DATA_FOLDER / "processed", DATA_FOLDER / "processed", Path("artifacts/"))
