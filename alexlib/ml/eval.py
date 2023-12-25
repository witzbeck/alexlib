from dataclasses import dataclass, field
from random import randint, random

from numpy import array

from alexlib.maths import combine_domains, interpolate, get_rect_area
from alexlib.maths import get_list_difs
from alexlib.time import timeit

if __name__ == "__main__":
    from alexlib.db import Connection

    cnxn = Connection()

roundto = 8
thresholds = [round(i / 100, roundto) for i in range(0, 101)]
rng = range(len(thresholds))


@timeit
def mk_test_probs(rng: range = rng):
    return [round(random(), roundto) for _ in rng]


@timeit
def mk_test_labels(rng: range = rng):
    return [randint(0, 1) for _ in rng]


@dataclass
class Rate:
    istrue: bool = field(default=True)
    ispositive: bool = field(default=True)
    probs: list = field(
        default_factory=list,
        repr=False,
    )
    labels: list = field(
        default_factory=list,
        repr=False,
    )
    thresholds: list = field(
        default_factory=list,
        repr=False,
    )

    def __post_init__(self):
        self.thresholds = thresholds

    @property
    def isfalse(self):
        return not self.istrue

    @property
    def isnegative(self):
        return not self.ispositive

    @property
    def affirm_val(self):
        if self.istrue and self.ispositive:
            return 1
        if self.istrue and self.isnegative:
            return 0
        elif self.isfalse and self.isnegative:
            return 1
        elif self.isfalse and self.ispositive:
            return 0

    @property
    def truecount(self):
        return self.labels.count(1)

    @property
    def falsecount(self):
        return self.labels.count(0)

    @property
    def n(self):
        return len(self.labels)

    @property
    def rng(self):
        return range(self.n)

    @property
    def count(self):
        return self.truecount if self.istrue else self.falsecount

    @staticmethod
    def get_predictions(
        probs: list[float],
        threshold: float,
    ):
        return [1 if p >= threshold else 0 for p in probs]

    @staticmethod
    def get_prediction_alignment(
        affirm_val: int,
        predictions: list[int],
        labels: list[int],
        rng: range,
    ):
        (
            p,
            l,
        ) = (
            predictions,
            labels,
        )
        return [(p[i] == l[i] == affirm_val) for i in rng]

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
    def rates(self):
        return array([self.get_rate(threshold) for threshold in thresholds])

    @classmethod
    def tp(
        cls,
        probs: list[float],
        labels: list[int],
    ):
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
    ):
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
    ):
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
    ):
        return cls(
            istrue=False,
            ispositive=False,
            probs=probs,
            labels=labels,
        )


@dataclass
class ROC:  # Receiver Operating Characteristic
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

    def __post_init__(self):
        self.tp = Rate.tp(self.probs, self.true_labels).rates
        self.fp = Rate.fp(self.probs, self.true_labels).rates

    @staticmethod
    def get_deltas(lst: list[float]):
        return [lst[i] - lst[i - 1] if i > 0 else lst[i] for i in rng]

    @property
    def fp_delta(self):
        return get_list_difs(self.fp)

    @property
    def tp_delta(self):
        return get_list_difs(self.tp)

    @property
    def auc(self):
        return sum([self.fp_delta[i] * self.tp[i] for i in rng])

    @staticmethod
    def mk_legend_text(
        auc: float,
        roundto: int = 2,
    ) -> str:
        val = round(auc, roundto)
        return f"AUC = {str(val)}"

    @property
    def legend_text(self):
        return self.mk_legend_text(self.auc)

    @timeit
    def plot(
        self,
        xlabel: str = "False Positive Rate",
        ylabel: str = "True Positive Rate",
        title: str = "ROC Curve",
    ):
        from matplotlib.pyplot import plot, title as t, show
        from matplotlib.pyplot import xlabel as x, ylabel as y, legend

        plot(self.fp, self.tp)
        x(xlabel), y(ylabel), t(title)
        legend([self.legend_text])
        show()

    @classmethod
    def rand(cls):
        return cls(
            true_labels=mk_test_labels(),
            probs=mk_test_probs(),
        )


class ABROCA:
    @timeit
    def __init__(self, roc1: ROC, roc2: ROC):
        self.roc1 = roc1
        self.roc2 = roc2
        self.domain = combine_domains(roc1.fp, roc2.fp)

    @property
    def domain_len(self):
        return len(self.domain)

    @property
    def domain_rng(self):
        return range(self.domain_len)

    @staticmethod
    def argidx(
        val: float,
        lookuplst: list[float],
        returnlst: list[float] = None,
    ):
        idx = lookuplst.index(val)
        if returnlst is None:
            ret = idx
        else:
            ret = returnlst[idx]
        return ret

    @staticmethod
    def get_one_smaller(
        val: float,
        lookuplst: list[float],
    ):
        return max([x for x in lookuplst if x < val])

    @staticmethod
    def get_one_smaller_idx(
        val: float,
        lookuplst: list[float],
    ):
        return lookuplst.index(ABROCA.get_one_smaller(val, lookuplst))

    @staticmethod
    def get_one_bigger(
        val: float,
        lookuplst: list[float],
    ):
        return min([x for x in lookuplst if x > val])

    @staticmethod
    def get_one_bigger_idx(
        val: float,
        lookuplst: list[float],
    ):
        return lookuplst.index(ABROCA.get_one_bigger(val, lookuplst))

    @staticmethod
    def get_interpolated_val(
        lookupval: float,
        target_roc: ROC,
    ):
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
        return [
            ABROCA.get_interpolated_val(
                val,
                roc,
            )
            for val in domain
        ]

    @timeit
    def set_new_tpr1(self):
        self.new_tpr1 = self.get_new_tpr(
            self.roc1,
            self.domain,
        )

    @timeit
    def set_new_tpr2(self):
        self.new_tpr2 = self.get_new_tpr(
            self.roc2,
            self.domain,
        )

    @staticmethod
    def get_domain_deltas(domain: list[float]):
        return get_list_difs(domain)

    @timeit
    def set_domain_deltas(self):
        self.domain_deltas = self.get_domain_deltas(self.domain)

    @staticmethod
    def get_combined_tpr_deltas(
        tpr1: list[float],
        tpr2: list[float],
        rng: range,
    ):
        return [tpr1[i] - tpr2[i] for i in rng]

    @timeit
    def set_combined_tpr_deltas(self):
        self.combined_tpr_deltas = self.get_combined_tpr_deltas(
            self.new_tpr1,
            self.new_tpr2,
            self.domain_rng,
        )

    @staticmethod
    def get_abroca(
        combined_tpr_deltas: list[float],
        domain_deltas: list[float],
    ):
        return get_rect_area(
            combined_tpr_deltas,
            domain_deltas,
        )

    @timeit
    def set_abroca(self):
        self.abroca = self.get_abroca(
            self.combined_tpr_deltas,
            self.domain_deltas,
        )

    def steps(self):
        self.set_new_tpr1()
        self.set_new_tpr2()
        self.set_domain_deltas()
        self.set_combined_tpr_deltas()
        self.set_abroca()

    @classmethod
    def rand(cls):
        return cls(
            roc1=ROC.rand(),
            roc2=ROC.rand(),
        )


if __name__ == "__main__":
    abroca = ABROCA.rand()
    # print(abroca.roc1.auc, abroca.roc1.fp)
    # print(abroca.roc2.auc, abroca.roc2.fp)
    print(len(abroca.domain), "domain")
    abroca.set_new_tpr1()
    print(len(abroca.new_tpr1), "new_tpr1")
    abroca.set_new_tpr2()
    print(len(abroca.new_tpr2), "new_tpr2")
    abroca.set_domain_deltas()
    print(abroca.domain_deltas.__class__.__name__, len(abroca.domain_deltas))
    abroca.set_combined_tpr_deltas()
    print(
        abroca.combined_tpr_deltas.__class__.__name__,
        len(abroca.combined_tpr_deltas)
    )
    abroca.set_abroca()
    # print(abroca.abroca)
