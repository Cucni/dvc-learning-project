from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.neighbors import KNeighborsClassifier

DATA_FOLDER = Path("data/")


def train(data_path: Path, artifact_folder: Path) -> None:
    train = pd.read_csv(data_path / "train_processed.csv")
    test = pd.read_csv(data_path / "test_processed.csv")
    target = "sex"

    X_train = train.drop(columns=[target])
    y_train = train[target]
    X_test = test.drop(columns=[target])
    y_test = test[target]

    knn = KNeighborsClassifier().fit(X_train, y_train)
    y_pred_train = knn.predict(X_train)
    y_pred_test = knn.predict(X_test)

    print("Accuracy train: {:.4f}".format(accuracy_score(y_pred_train, y_train)))
    print("Accuracy test: {:.4f}".format(accuracy_score(y_pred_test, y_test)))

    joblib.dump(knn, artifact_folder / "model.joblib")


if __name__ == "__main__":
    train(DATA_FOLDER / "processed", Path("artifacts/"))
