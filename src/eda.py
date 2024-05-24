# %%
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

DATA_FOLDER = Path("../data/")

# %%

# Dictionaries for translating coded column entries into readable values

AQUACULTURE_METHODS = {
    "PON": "Ponds",
    "TNK": "Tanks and raceways",
    "ENC": "Enclosures and pens",
    "CAG": "Cages",
    "RES": "Recirculation systems",
    "ONB": "On bottom",
    "OFB": "Off bottom",
    "OTH": "Other methods",
    "NSP": " Not specified",
}

AQUATIC_ENVIRONMENTS = {
    "FRW": "Freshwater",
    "SBW": "Sea and brackish water (total)",
    "SEA": "Seawater",
    "BRK": "Brackish water",
    "NSP": " Not specified",
}


FISHING_REGIONS = {
    9: "Inland waters - Total",
    1: "Inland waters - Africa",
    4: "Inland waters - Asia",
    5: "Inland waters - Europe",
    10: "Marine areas",
    27: "Atlantic, Northeast",
    34: "Atlantic, Eastern Central",
    37: "Mediterranean and Black Sea",
    "NSP": "Area not specified",
}

UNITS = {"EUR": "Euro", "EUR_T": "Euro per tonne", "TLW": " Tonnes live weight"}


COUNTRY_CODES = {
    "BE": "Belgium",
    "BG": "Bulgaria",
    "CZ": "Czechia",
    "DK": "Denmark",
    "DE": "Germany",
    "EE": "Estonia",
    "IE": "Ireland",
    "EL": "Greece",
    "ES": "Spain",
    "FR": "France",
    "HR": "Croatia",
    "IT": "Italy",
    "CY": "Cyprus",
    "LV": "Latvia",
    "LT": "Lithuania",
    "HU": "Hungary",
    "MT": "Malta",
    "NL": "Netherlands",
    "AT": "Austria",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "FI": "Finland",
    "SE": "Sweden",
    "IS": "Iceland",
    "NO": "Norway",
    "UK": "United Kingdom",
    "BA": "Bosnia and Herzegovina",
    "ME": "Montenegro",
    "MK": "North Macedonia",
    "AL": "Albania",
    "RS": "Serbia",
    "TR": "Turkey",
}

# %%

# Loading data

df = pd.read_csv(DATA_FOLDER / "fish_aq2a_custom_linear.csv")

# %%

# Data cleaning

# Uniformise column names

df = df.rename(columns=lambda x: x.lower().replace(" ", "_"))

# Cast last update time to a timestamp dtype
df = df.astype({"last_update": "datetime64[ns]"})

df

# %%
# Find constant columns. These do not provide any information
df.columns[df.nunique() == 1]

# %% [markdown]
# We see that the columns "dataflow", "last_update", "freq" and "time_period" always contain the same value. Of these:
# * "dataflow" and "last_update" contain metadata about the dataset identifier and the timestamp of last update.
# * "freq" indicates that the reporting frequency is yearly for all the monitored aquacultures.
# * "year" indicates that the reporting year is 2022, which we already knew.
#
# As we are not joining data from various sources or years, we can safely drop all these columns.

# %%
df = df.drop(columns=df.columns[df.nunique() == 1])

# %%

# According to the documentation, when the observation flag is "c" the datum is confidential and thus not reported. Let's check what the dataset contains in this case.
# %%
df.loc[df.obs_flag == "c", "obs_value"].isna().mean()

# %%
# As documented, for all records with observation flag equal to "c" the numeric value is replaced by NaN. We cannot extract any info from these (except the existence of that aquaculture), so we drop these records.
df = df.loc[~(df.obs_flag == "c"), :]

df.obs_value.isna().sum()
# %%
# At this point there are no more missing values from the observation column. The observation flag can further obtain the values "n" and "e". The former means that the production is not significant, and the value is accordingly reported as 0. The latter is instead undocumented, but we can see that it corresponds to populated values, all from freshwater ponds. We will keep these records as they are. The flag column can then be dropped at this point.

# %%
display(df[df.obs_flag == "n"])
display(df[df.obs_flag == "e"])
df = df.drop(columns=["obs_flag"])

# %%
# The columns "aquameth", "aquaenv" and "fishreg" can contain the string "NSP" standing for "not specified". We transform these into NaNs.
for col in ["aquameth", "aquaenv", "fishreg"]:
    df.loc[df[col] == "NSP", col] = np.nan

df.isna().any(axis=1).mean()

# We can see that 15% of the records now report a missing value. In general one could think about how to impute these. Options include lumping them together with "other" for fields that admit it, using a machine learning classifier, looking up older data, etc. As this is a learning project, we will drop them for simplicity.

# %%
df = df.dropna()
# %%
df.shape

# %% [markdown]
# Since this is a learning project, we are not going to do an in-depth EDA, and will instead mostly accept the data as-is. There are however three important aspects to cover:
# * the "fishreg" column is encoded with integers, but these act as codes, they don't carry any numerical meaning. For this reason it is better to avoid having a numerical column, otherwise a machine learning algorithm could pick up spurious relationships. We will then translate this column using a dictionary, so that it will act as a categorical feature.
# * the dataset contains records for the amount of tonnes fished, value fished in Euros and value per tonne in Euros. We are interested in predicting the amount of tonnes fished, so we will restrict to these records only
# * the fish species F00, F01 and F08 are totals computed from the sum of the other quantities, so we will drop these records and only keep species F02, F04 and F07 (freshwater fish, shellfish and finfish respectively)

# %%

# Encode fishing region as a category
df["fishreg"] = df["fishreg"].astype(int).replace(FISHING_REGIONS)

# %%
df = df.loc[(df.unit == "TLW") & (df["species"].isin(["F02", "F04", "F07"])), :]

# %%
df = df.astype(
    {
        "aquameth": "category",
        "aquaenv": "category",
        "species": "category",
        "fishreg": "category",
        "geo": "category",
    }
).drop(columns=["unit"])

# %%
# This concludes the data preparation. Let's now train a quick model to close the circle.

rf = RandomForestRegressor()
# %%
X_train, X_test, y_train, y_test = train_test_split(
    df.drop(columns=["obs_value"]),
    df["obs_value"],
    train_size=0.80,
    random_state=10,
    shuffle=True,
)
# %%
rf.train(X_train, y_train)
