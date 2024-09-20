from dataclasses import dataclass, field

from numpy import array, ravel
from pandas import DataFrame
from scipy.stats import expon, uniform
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import (
    GridSearchCV,
    ParameterGrid,
    ParameterSampler,
    RandomizedSearchCV,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from alexlib.core import chkenv, datetime
from alexlib.db import Connection
from alexlib.df import filter_df, get_distinct_col_vals
from alexlib.files.config import DotEnv
from alexlib.iters import keys, link
from alexlib.maths import discrete_exp_dist

config = DotEnv()
cnxn = Connection()

model_types = chkenv("MODEL_TYPES", type=list)


@dataclass
class Features:
    to_predict_col: str = field(default=chkenv("TO_PREDICT_COL"))
    schema: str = field(default=chkenv("FEATURE_SCHEMA"))
    table: str = field(default=chkenv("FEATURE_TABLE"))
    nrows: str = field(default=chkenv("NROWS", type=int, required=False))
    to_exclude: list = field(default_factory=list)
    to_include: list = field(default_factory=list)
    cnxn: Connection = field(default_factory=Connection)
    df: DataFrame = field(default_factory=DataFrame)
    df_filter: list[tuple] = field(default_factory=list)
    info_schema: DataFrame = field(default_factory=DataFrame)
    dtypes: dict = field(default_factory=dict)

    @property
    def drop_cols(self):
        r = chkenv("DROP_COLS", type=list)
        res_cols = [x for x in r if x != self.to_predict_col]
        return link(
            [
                self.to_exclude,
                res_cols,
            ]
        )

    @property
    def tbl(self):
        return self.cnxn.get_table(
            self.schema,
            self.table,
            nrows=self.nrows,
        )

    def get_info_schema(self):
        return self.cnxn.get_info_schema(
            self.schema,
            self.table,
        )

    def set_info_schema(self):
        self.info_schema = self.get_info_schema()

    def __post_init__(self):
        self.df = self.tbl
        self.set_info_schema()
        self.set_dtypes()

    @property
    def dtype_df(self):
        return self.info_schema.loc[:, ["column_name", "data_type"]]

    def get_dtypes(self):
        return self.dtype_df.set_index("column_name").to_dict()["data_type"]

    def set_dtypes(self):
        self.dtypes = self.get_dtypes()

    @property
    def cols(self):
        return list(self.df.columns)

    def isin(self, col: str):
        return col in self.to_include

    def isex(self, col: str):
        return col in self.to_exclude

    def innotex(self, col: str):
        return self.isin(col) and not self.isex(col)

    @property
    def features(self):
        ret = [x for x in self.cols if self.innotex(x)]
        return [x for x in ret if x not in self.drop_cols]

    def get_dtype(self, col: str):
        return self.dtypes[col]

    def iscat(self, col: str):
        return self.get_dtype(col) in ["character varying"]

    def isnum(self, col: str):
        return self.get_dtype(col) in [
            "integer",
            "double precision",
            "numeric",
            "bigint",
        ]

    def isbool(self, col: str) -> bool:
        return self.get_dtype(col) in ["boolean", "bit"]

    @property
    def catcols(self) -> list[str]:
        return [x for x in self.features if self.iscat(x)]

    @property
    def numcols(self) -> list[str]:
        return [x for x in self.features if self.isnum(x)]

    @property
    def boolcols(self) -> list[str]:
        return [x for x in self.features if self.isbool(x)]

    @property
    def feat_df(self) -> DataFrame:
        return self.df.loc[:, self.features]

    @property
    def nfilters(self) -> int:
        return len(self.df_filter)

    @property
    def filtered_df(self):
        df = self.df
        for col, val in self.df_filter:
            df = filter_df(self.df, col, val)
        return df

    @property
    def nfeatures(self):
        return len(self.features)

    @property
    def now(self):
        return datetime.now()

    @property
    def logdict(self):
        nextid = self.cnxn.get_next_id(self.schema, self.table, "id")
        return {
            "id": nextid,
            "context": self.cnxn.context,
            "schema": self.schema,
            "table": self.table,
            "col": self.col,
            "nfeatures": self.nfeatures,
            "to_exclude": ",".join(self.to_exclude),
            "to_include": ",".join(self.to_include),
            "created_at": self.now,
        }


@dataclass
class Pipe:
    name: str
    obj: object

    @property
    def _keys(self):
        return keys(self.__dict__)

    @property
    def _attrs(self):
        return [x for x in self._keys if x not in ["name", "obj"]]

    @property
    def kwargs(self):
        return {x: getattr(self, x) for x in self._attrs}

    @property
    def haskwargs(self):
        return len(self.kwargs) > 0

    @property
    def step(self):
        return (self.name, self.obj(**self.kwargs))


@dataclass
class ScalerStep(Pipe):
    name: str = field(default="scaler")
    obj: object = field(default=StandardScaler)


@dataclass
class ImputerStep(Pipe):
    name: str = field(default="imputer")
    obj: object = field(default=SimpleImputer)
    strategy: str = field(default="constant")
    fill_value: int = field(default=0)


@dataclass
class OneHotStep(Pipe):
    name: str = field(default="onehot")
    obj: object = field(default=OneHotEncoder)
    handle_unknown: str = field(default="ignore")


@dataclass
class DataPipeline:
    steps: list = field(default_factory=list)

    def add_step(self, step: Pipe):
        self.steps.append(step.step)

    @property
    def pipeline(self):
        return Pipeline(self.steps)


@dataclass
class CategoricalPipeline(DataPipeline):
    def __post_init__(self):
        self.add_step(ImputerStep())
        self.add_step(OneHotStep())


@dataclass
class NumericPipeline(DataPipeline):
    def __post_init__(self):
        self.add_step(ImputerStep())
        self.add_step(ScalerStep())


@dataclass
class BooleanPipeline(DataPipeline):
    def __post_init__(self):
        self.add_step(ImputerStep())


@dataclass
class DataPreprocessor:
    feat: Features = field(default_factory=Features)
    cat: DataPipeline = field(
        default_factory=CategoricalPipeline,
        repr=False,
    )
    num: DataPipeline = field(
        default_factory=NumericPipeline,
        repr=False,
    )
    bool: DataPipeline = field(
        default_factory=BooleanPipeline,
        repr=False,
    )
    remainder: str = field(default="passthrough")
    test_size: float = field(default=chkenv("TEST_SIZE", type=float))
    random_state: int = field(
        default=chkenv("RANDOM_STATE", type=int, required=False),
    )
    X_train: array = field(default_factory=array)
    X_test: array = field(default_factory=array)
    y_train: array = field(default_factory=array)
    y_test: array = field(default_factory=array)

    def get_data(self):
        return self.feat.filtered_df

    def set_data(self):
        self.data = self.get_data()

    @property
    def predictors(self):
        return [x for x in self.feat.features if x != self.feat.to_predict_col]

    @property
    def y(self):
        return ravel(self.data.loc[:, self.feat.to_predict_col])

    @property
    def X(self):
        return self.data.loc[:, self.predictors]

    def set_testtrain(self):
        xtr, xts, ytr, yts = train_test_split(
            self.X,
            self.y,
            test_size=self.test_size,
            random_state=self.random_state,
        )
        self.X_train = xtr
        self.X_test = xts
        self.y_train = ytr
        self.y_test = yts

    def __post_init__(self):
        self.set_data()
        self.set_testtrain()

    @property
    def coltransformer(self):
        return ColumnTransformer(
            [
                ("cat", self.cat.pipeline, self.feat.catcols),
                ("num", self.num.pipeline, self.feat.numcols),
                ("bool", self.bool.pipeline, self.feat.boolcols),
            ],
            remainder=self.remainder,
        )

    @property
    def ncat(self):
        return len(self.cat_cols)

    @property
    def nnum(self):
        return len(self.num_cols)

    @property
    def nbool(self):
        return len(self.bool_cols)


@dataclass
class Parameters:
    model_type: str = field(default=chkenv("MODEL_TYPE"))
    params: dict = field(default_factory=dict)
    predict_col: str = field(default=chkenv("TO_PREDICT_COL"))
    nrows: int = field(default=chkenv("NROWS", type=int, required=False))
    random_state: int = field(default=chkenv("RANDOM_STATE", type=int))
    pre_dispatch: str = field(default=chkenv("PRE_DISPATCH"))
    niter: int = field(default=chkenv("SEARCH_ITER", type=int))
    randomsearch: bool = field(default=chkenv("RANDOM_SEARCH", type=bool))
    groupedsearch: bool = field(default=chkenv("GROUPED_SEARCH", type=bool))
    n_jobs: int = field(default=chkenv("N_JOBS", type=int))
    warm_start: bool = field(default=chkenv("WARM_START", type=bool))

    @property
    def cv(self):
        if self.randomsearch:
            ret = RandomizedSearchCV
        else:
            ret = GridSearchCV
        return ret

    @property
    def sampler(self):
        if self.randomsearch:
            ret = ParameterSampler
        else:
            ret = ParameterGrid
        return ret

    @property
    def paramdict(self):
        _bool = [True, False]
        uni = uniform()
        discrete_uni = [i / 10 for i in range(1, 10, 2)]
        _dict = {
            "logreg": [
                {
                    "clf__solver": ["lbfgs", "sag", "newton-cg", "newton-cholesky"],
                    "clf__penalty": [None, "l2"],
                    "clf__C": expon(scale=0.1),
                    "clf__warm_start": [False],
                    "clf__max_iter": [i for i in range(30, 150)],
                    "clf__random_state": [self.random_state],
                    "clf__n_jobs": [self.n_jobs],
                },
                {
                    "clf__solver": ["saga"],
                    "clf__penalty": [None, "l2", "l1"],
                    "clf__C": expon(scale=0.1),
                    "clf__l1_ratio": uni,
                    "clf__warm_start": _bool,
                    "clf__random_state": [self.random_state],
                    "clf__n_jobs": [-1],
                },
                {
                    "clf__solver": ["saga"],
                    "clf__penalty": ["elasticnet"],
                    "clf__C": expon(scale=0.1),
                    "clf__l1_ratio": uni,
                    "clf__warm_start": _bool,
                    "clf__random_state": [self.random_state],
                    "clf__n_jobs": [self.n_jobs],
                },
                {
                    "clf__solver": ["liblinear"],
                    "clf__penalty": ["l1", "l2"],
                    "clf__C": expon(scale=0.1),
                    "clf__warm_start": _bool,
                    "clf__random_state": [self.random_state],
                },
            ],
            "svc": {
                "clf__C": expon(scale=0.1),
                "clf__kernel": ["linear", "rbf", "poly", "sigmoid"],
                "clf__degree": [i for i in range(1, 5)],
                "clf__probability": [True],
                "clf__gamma": ["auto", "scale"],
                "clf__random_state": [self.random_state],
            },
            "knn": {
                "clf__n_neighbors": [i for i in range(2, 6)],
                "clf__weights": ["uniform", "distance"],
                "clf__algorithm": ["auto", "ball_tree", "kd_tree", "brute"],
                "clf__leaf_size": [i for i in range(10, 100)],
                "clf__p": [i for i in range(1, 5)],
                "clf__n_jobs": [self.n_jobs],
            },
            "dtree": {
                "clf__criterion": ["gini", "entropy", "log_loss"],
                "clf__splitter": ["best", "random"],
                "clf__max_depth": [i for i in range(10, 100)],
                "clf__min_samples_leaf": [i for i in range(1, 10)],
                "clf__min_samples_split": [i for i in range(2, 100)],
                "clf__max_features": [None, "sqrt", "log2"],
                "clf__random_state": [self.random_state],
            },
            "etree": {
                "clf__criterion": ["gini", "entropy", "log_loss"],
                "clf__n_estimators": [i for i in range(10, 200)],
                "clf__max_features": [None, "sqrt", "log2"],
                "clf__min_samples_split": [i for i in range(2, 10)],
                "clf__min_samples_leaf": [i for i in range(1, 10)],
                "clf__bootstrap": [True],
                "clf__oob_score": [True],
                "clf__warm_start": _bool,
                "clf__max_samples": uniform(),
                "clf__random_state": [self.random_state],
                "clf__n_jobs": [self.n_jobs],
            },
            "rforest": {
                "clf__criterion": ["gini", "entropy", "log_loss"],
                "clf__n_estimators": [i for i in range(10, 200)],
                "clf__min_samples_split": [i for i in range(2, 10)],
                "clf__min_samples_leaf": [i for i in range(1, 10)],
                "clf__max_features": [None, "sqrt", "log2"],
                "clf__bootstrap": [True],
                "clf__oob_score": [True],
                "clf__warm_start": _bool,
                "clf__max_samples": uniform(),
                "clf__random_state": [self.random_state],
                "clf__n_jobs": [self.n_jobs],
            },
            "mlp": {
                "clf__hidden_layer_sizes": [i for i in range(10, 200)],
                "clf__activation": ["identity", "logistic", "tanh", "relu"],
                "clf__solver": ["adam", "lbfgs", "sgd"],
                "clf__learning_rate": ["constant", "adaptive", "invscaling"],
                "clf__learning_rate_init": expon(scale=0.01),
                "clf__power_t": expon(scale=0.1),
                "clf__alpha": expon(scale=0.01),
                "clf__max_iter": [i for i in range(30, 150)],
                "clf__warm_start": _bool,
                "clf__early_stopping": _bool,
                "clf__random_state": [self.random_state],
            },
            "hxg_boost": {
                "clf__random_state": [self.random_state],
                "clf__learning_rate": expon(scale=0.01),
                "clf__max_iter": [i for i in range(30, 150)],
                "clf__max_depth": [i for i in range(10, 100)],
                "clf__max_bins": [i for i in range(100, 256)],
                "clf__warm_start": _bool,
                "clf__l2_regularization": uniform(),
                "clf__min_samples_leaf": [i for i in range(1, 10)],
                "clf__interaction_cst": ["pairwise", "no_interactions"],
            },
            "ada_boost": {
                "clf__random_state": [self.random_state],
                "clf__learning_rate": expon(scale=0.01),
            },
            "xg_boost": {
                "clf__random_state": [self.random_state],
            },
            "compnb": {
                "clf__alpha": expon(scale=0.01),
                "clf__norm": _bool,
            },
            "gauss": {
                "clf__random_state": [self.random_state],
            },
        }
        _dict = _dict[self.model_type]
        _keys = keys(_dict)

        def innotrand(x: str) -> bool:
            return x in _keys and not self.randomsearch

        if innotrand("clf__learning_rate") and self.model_type != "mlp":
            _dict.update({"clf__learning_rate": discrete_exp_dist(1, 4)})
        if innotrand("clf__C"):
            _dict.update({"clf__C": discrete_exp_dist(-2, 2)})
        if innotrand("clf__l1_ratio"):
            _dict.update({"clf__l1_ratio": discrete_uni})
        if innotrand("clf__max_samples"):
            _dict.update({"clf__max_samples": discrete_uni})
        if innotrand("clf__learning_rate_init"):
            _dict.update({"clf__learning_rate_init": discrete_exp_dist(1, 2)})
        if innotrand("clf__power_t"):
            _dict.update({"clf__power_t": discrete_exp_dist(1, 2)})
        if innotrand("clf__alpha"):
            _dict.update({"clf__alpha": discrete_exp_dist(1, 2)})
        if innotrand("clf__l2_regularization"):
            _dict.update({"clf__l2_regularization": discrete_exp_dist(1, 2)})
        return _dict


if __name__ == "__main__":
    feat = Features()
    print(get_distinct_col_vals(feat.info_schema, "data_type"))
