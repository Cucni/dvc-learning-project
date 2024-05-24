from pathlib import Path

import joblib
import pandas as pd
import yaml
from sklearn.metrics import accuracy_score

DATA_FOLDER = Path("data/")
PARAMS_FILE = Path("params.yaml")


def evaluate(data_file: Path, model_file: Path) -> None:
    df = pd.read_csv(data_file)
    target = "sex"

    X = df.drop(columns=[target])
    y = df[target]

    lr = joblib.load(model_file)

    y_pred = lr.predict(X)

    print("Accuracy: {:.4f}".format(accuracy_score(y_pred, y)))


if __name__ == "__main__":
    # Load parameters from params.yaml
    with open(PARAMS_FILE, "r") as params_file:
        params = yaml.safe_load(params_file)["evaluate"]
    evaluate(
        DATA_FOLDER / "processed" / Path(params["test_dataset_name"]),
        Path("artifacts/model.joblib"),
    )
