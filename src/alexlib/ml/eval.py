"""Evaluation metrics for machine learning."""

from dataclasses import dataclass, field
from random import randint, random

from matplotlib.pyplot import legend, plot, show, title, xlabel, ylabel
from numpy import array, ndarray

from alexlib.maths import combine_domains, get_list_difs, get_rect_area, interpolate
from alexlib.times import timeit

if __name__ == "__main__":
    from alexlib.db import Connection

    cnxn = Connection()

ROUNDTO, NTHRESHOLDS = 8, 100
rng = range(NTHRESHOLDS + 1)


def mk_thresholds(
    n: int = NTHRESHOLDS,
    roundto: int = ROUNDTO,
) -> list[float]:
    """Make a list of thresholds."""
    return [round(i / n, roundto) for i in range(n + 1)]


@timeit
def mk_test_probs(rng: range = rng) -> list[float]:
    """Make a list of random probabilities."""
    return [round(random(), ROUNDTO) for _ in rng]


@timeit
def mk_test_labels(rng: range = rng) -> list[int]:
    """Make a list of random labels."""
    return [randint(0, 1) for _ in rng]


@dataclass
class Rate:
    """A rate is a true positive rate or a false positive rate."""

    istrue: bool = field(default=True)
    ispositive: bool = field(default=True)
    probs: list = field(
        default_factory=mk_test_probs,
        repr=False,
    )
    labels: list = field(
        default_factory=mk_test_labels,
        repr=False,
    )
    thresholds: list = field(
        default_factory=mk_thresholds,
        repr=False,
    )

    @property
    def isfalse(self) -> bool:
        """Check if a rate is false."""
        return not self.istrue

    @property
    def isnegative(self) -> bool:
        """Check if a rate is negative."""
        return not self.ispositive

    @property
    def affirm_val(self) -> int:
        """Get the affirm value of a rate."""
        if self.istrue and self.ispositive:
            ret = 1
        if self.istrue and self.isnegative:
            ret = 0
        elif self.isfalse and self.isnegative:
            ret = 1
        elif self.isfalse and self.ispositive:
            ret = 0
        return ret

    @property
    def truecount(self) -> int:
        """Get the number of true labels."""
        return self.labels.count(1)

    @property
    def falsecount(self) -> int:
        """Get the number of false labels."""
        return self.labels.count(0)

    @property
    def n(self) -> int:
        """Get the number of labels."""
        return len(self.labels)

    @property
    def rng(self) -> range:
        """Get the range of labels."""
        return range(self.n)

    @property
    def count(self) -> int:
        """Get the number of labels."""
        return self.truecount if self.istrue else self.falsecount

    @staticmethod
    def get_predictions(
        probs: list[float],
        threshold: float,
    ) -> list[int]:
        """Get the predictions from a list of probabilities."""
        return [1 if p >= threshold else 0 for p in probs]

    @staticmethod
    def get_prediction_alignment(
        affirm_val: int,
        predictions: list[int],
        labels: list[int],
    ) -> list[bool]:
        """Get the alignment of predictions and labels."""
        return [pred == lab == affirm_val for pred, lab in zip(predictions, labels)]

    def get_rate(self, threshold: float):
        predictions = self.get_predictions(
            probs=self.probs,
            threshold=threshold,
        )
        alignment = Rate.get_prediction_alignment(
            self.affirm_val,
            predictions,
            self.labels,
            self.rng,
        )
        return sum(alignment) / self.count

    @property
    def rates(self) -> ndarray:
        """Get the rates."""
        return ndarray([self.get_rate(threshold) for threshold in self.thresholds])

    @classmethod
    def tp(
        cls,
        probs: list[float],
        labels: list[int],
    ) -> "Rate":
        """Get a true positive rate."""
        return cls(
            istrue=True,
            ispositive=True,
            probs=probs,
            labels=labels,
        )

    @classmethod
    def fp(
        cls,
        probs: list[float],
        labels: list[int],
    ) -> "Rate":
        """Get a false positive rate."""
        return cls(
            istrue=False,
            ispositive=True,
            probs=probs,
            labels=labels,
        )

    @classmethod
    def tn(
        cls,
        probs: list[float],
        labels: list[int],
    ) -> "Rate":
        """Get a true negative rate."""
        return cls(
            istrue=True,
            ispositive=False,
            probs=probs,
            labels=labels,
        )

    @classmethod
    def fn(
        cls,
        probs: list[float],
        labels: list[int],
    ) -> "Rate":
        """Get a false negative rate."""
        return cls(
            istrue=False,
            ispositive=False,
            probs=probs,
            labels=labels,
        )


@dataclass
class ROC:
    """Receiver Operating Characteristic"""

    true_labels: list[int] = field(
        default_factory=list,
        repr=False,
    )
    probs: list[float] = field(
        default_factory=list,
        repr=False,
    )
    tp: array[float] = field(
        default_factory=array,
        repr=False,
    )
    fp: array[float] = field(
        default_factory=array,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Initialize the ROC."""
        self.tp = Rate.tp(self.probs, self.true_labels).rates
        self.fp = Rate.fp(self.probs, self.true_labels).rates

    @staticmethod
    def get_deltas(lst: list[float]) -> list[float]:
        """Get the deltas of a list."""
        return [lst[i] - lst[i - 1] if i > 0 else lst[i] for i in rng]

    @property
    def fp_delta(self) -> list[float]:
        """Get the false positive rate deltas."""
        return get_list_difs(self.fp)

    @property
    def tp_delta(self) -> list[float]:
        """Get the true positive rate deltas."""
        return get_list_difs(self.tp)

    @property
    def auc(self) -> float:
        """Get the area under the curve."""
        return sum([self.fp_delta[i] * self.tp[i] for i in rng])

    @staticmethod
    def mk_legend_text(
        auc: float,
        roundto: int = 2,
    ) -> str:
        """Make the legend text."""
        val = round(auc, roundto)
        return f"AUC = {str(val)}"

    @property
    def legend_text(self) -> str:
        """Get the legend text."""
        return self.mk_legend_text(self.auc)

    @timeit
    def plot(
        self,
        xlabel_: str = "False Positive Rate",
        ylabel_: str = "True Positive Rate",
        title_: str = "ROC Curve",
    ) -> None:
        """Plot the ROC."""
        plot(self.fp, self.tp)
        xlabel(xlabel_), ylabel(ylabel_), title(title_)
        legend([self.legend_text])
        show()

    @classmethod
    def rand(cls) -> "ROC":
        """Get a random ROC."""
        return cls(
            true_labels=mk_test_labels(),
            probs=mk_test_probs(),
        )


class ABROCA:
    """Area Between Receiver Operating Characteristic Curves"""

    @timeit
    def __init__(self, roc1: ROC, roc2: ROC) -> None:
        """Initialize the ABROCA."""
        self.roc1 = roc1
        self.roc2 = roc2
        self.domain = combine_domains(roc1.fp, roc2.fp)

    @property
    def domain_len(self) -> int:
        """Get the length of the domain."""
        return len(self.domain)

    @property
    def domain_rng(self) -> range:
        """Get the range of the domain."""
        return range(self.domain_len)

    @staticmethod
    def argidx(
        val: float,
        lookuplst: list[float],
        returnlst: list[float] = None,
    ) -> int:
        """Get the index of a value in a list."""
        idx = lookuplst.index(val)
        return idx if returnlst is None else returnlst[idx]

    @staticmethod
    def get_one_smaller(
        val: float,
        lookuplst: list[float],
    ) -> float:
        """Get the value in a list that is one smaller than a value."""
        return max(x for x in lookuplst if x < val)

    @staticmethod
    def get_one_smaller_idx(
        val: float,
        lookuplst: list[float],
    ) -> int:
        """Get the index of a value in a list that is one smaller than a value."""
        return lookuplst.index(ABROCA.get_one_smaller(val, lookuplst))

    @staticmethod
    def get_one_bigger(
        val: float,
        lookuplst: list[float],
    ) -> float:
        """Get the value in a list that is one bigger than a value."""
        return min(x for x in lookuplst if x > val)

    @staticmethod
    def get_one_bigger_idx(
        val: float,
        lookuplst: list[float],
    ) -> int:
        """Get the index of a value in a list that is one bigger than a value."""
        return lookuplst.index(ABROCA.get_one_bigger(val, lookuplst))

    @staticmethod
    def get_interpolated_val(
        lookupval: float,
        target_roc: ROC,
    ) -> float:
        """Get the interpolated value."""
        if lookupval in target_roc.fp:
            try:
                ret = ABROCA.argidx(
                    lookupval,
                    target_roc.fp,
                    returnlst=target_roc.tp,
                )
            except IndexError:
                ret = ABROCA.argidx(
                    lookupval,
                    target_roc.fp,
                )
        elif lookupval < target_roc.fp[0]:
            ret = 0
        elif lookupval > target_roc.fp[-1]:
            ret = 1
        else:
            idx = ABROCA.get_one_smaller_idx(
                lookupval,
                target_roc.fp,
            )
            ret = interpolate(
                lookupval,
                target_roc.fp[idx],
                target_roc.fp[idx + 1],
                target_roc.tp[idx],
                target_roc.tp[idx + 1],
            )
        return ret

    @staticmethod
    def get_new_tpr(
        roc: ROC,
        domain: list[float],
    ) -> list[float]:
        """Get the new true positive rate."""
        return [
            ABROCA.get_interpolated_val(
                val,
                roc,
            )
            for val in domain
        ]

    @timeit
    def set_new_tpr1(self) -> None:
        """Set the new true positive rate for roc1."""
        self.new_tpr1 = self.get_new_tpr(
            self.roc1,
            self.domain,
        )

    @timeit
    def set_new_tpr2(self) -> None:
        """Set the new true positive rate for roc2."""
        self.new_tpr2 = self.get_new_tpr(
            self.roc2,
            self.domain,
        )

    @staticmethod
    def get_domain_deltas(domain: list[float]) -> list[float]:
        """Get the domain deltas."""
        return get_list_difs(domain)

    @timeit
    def set_domain_deltas(self) -> None:
        """Set the domain deltas."""
        self.domain_deltas = self.get_domain_deltas(self.domain)

    @staticmethod
    def get_combined_tpr_deltas(
        tpr1: list[float],
        tpr2: list[float],
        rng: range,
    ) -> list[float]:
        """Get the combined true positive rate deltas."""
        return [tpr1[i] - tpr2[i] for i in rng]

    @timeit
    def set_combined_tpr_deltas(self) -> None:
        """Set the combined true positive rate deltas."""
        self.combined_tpr_deltas = self.get_combined_tpr_deltas(
            self.new_tpr1,
            self.new_tpr2,
            self.domain_rng,
        )

    @staticmethod
    def get_abroca(
        combined_tpr_deltas: list[float],
        domain_deltas: list[float],
    ) -> float:
        """Get the area between receiver operating characteristic curves."""
        return get_rect_area(
            combined_tpr_deltas,
            domain_deltas,
        )

    @timeit
    def set_abroca(self) -> None:
        """Set the area between receiver operating characteristic curves."""
        self.abroca = self.get_abroca(
            self.combined_tpr_deltas,
            self.domain_deltas,
        )

    def steps(self) -> None:
        """Run all the steps."""
        self.set_new_tpr1()
        self.set_new_tpr2()
        self.set_domain_deltas()
        self.set_combined_tpr_deltas()
        self.set_abroca()

    @classmethod
    def rand(cls) -> "ABROCA":
        """Get a random ABROCA."""
        return cls(
            roc1=ROC.rand(),
            roc2=ROC.rand(),
        )
