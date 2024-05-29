from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import yaml
from dvclive import Live
from sklearn.inspection import permutation_importance
from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay, accuracy_score

plt.style.use("ggplot")

DATA_FOLDER = Path("data/")
PARAMS_FILE = Path("params.yaml")


def evaluate(data_file: Path, model_file: Path, live_context: Live) -> None:
    df = pd.read_csv(data_file)
    target = "sex"

    X = df.drop(columns=[target])
    y = df[target]

    lr = joblib.load(model_file)

    y_pred = lr.predict(X)
    # Obtain predicted probability for the positive class
    proba_pred = lr.predict_proba(X)[:, 1]

    accuracy = accuracy_score(y, y_pred)
    feature_importance = permutation_importance(lr, X, y)
    feature_importance_df = pd.DataFrame(
        data={
            "feature_names": X.columns,
            "feature_importance": feature_importance.importances_mean,
        }
    )

    with plt.rc_context({"axes.grid": False}):
        confusion_matrix = ConfusionMatrixDisplay.from_predictions(y, y_pred)
        plt.tight_layout()
    live_context.log_image("precomputed_confusion_matrix.png", confusion_matrix.figure_)

    roc_curve = RocCurveDisplay.from_predictions(y, proba_pred)
    plt.tight_layout()
    live_context.log_image("precomputed_roc_curve.png", roc_curve.figure_)

    feature_importance_barplot = feature_importance_df.plot(
        kind="barh", y="feature_importance", x="feature_names"
    )
    plt.tight_layout()

    live_context.log_image(
        "precomputed_feature_importance.png", feature_importance_barplot.figure
    )

    live_context.log_metric("accuracy", accuracy, timestamp=True)
    live_context.log_sklearn_plot("confusion_matrix", y, y_pred, "DVC confusion matrix")
    live_context.log_sklearn_plot("roc", y, proba_pred, "DVC ROC curve")
    live_context.log_plot(
        "feature importance",
        feature_importance_df,
        y="feature_names",
        x="feature_importance",
        template="bar_horizontal",
    )

    print("Accuracy: {:.4f}".format(accuracy))


if __name__ == "__main__":
    # Load parameters from params.yaml
    with open(PARAMS_FILE, "r") as params_file:
        params = yaml.safe_load(params_file)["evaluate"]

    with Live(dir="eval", report="md") as live_context:
        evaluate(
            DATA_FOLDER / "processed" / Path(params["test_dataset_name"]),
            Path("artifacts/model.joblib"),
            live_context,
        )
