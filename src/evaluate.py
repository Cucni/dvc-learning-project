from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score

DATA_FOLDER = Path("data/")


def train(data_file: Path, model_file: Path) -> None:
    df = pd.read_csv(data_file)
    target = "sex"

    X = df.drop(columns=[target])
    y = df[target]

    lr = joblib.load(model_file)

    y_pred = lr.predict(X)

    print("Accuracy: {:.4f}".format(accuracy_score(y_pred, y)))


if __name__ == "__main__":
    train(
        DATA_FOLDER / "processed" / "test_processed.csv", Path("artifacts/model.joblib")
    )
