"""
Conditional Distribution Similarity Statistic
Used to infer causal directions
Author : José A.R. Fonollosa
Ref : Fonollosa, José AR, "Conditional distribution variability measures for causality detection", 2016.
"""

import numpy as np
from collections import Counter
from .model import Pairwise_Model

BINARY = "Binary"
CATEGORICAL = "Categorical"
NUMERICAL = "Numerical"


def count_unique(x):
    try:
        return len(set(x))
    except TypeError as e:
        print(x)
        raise e


def numerical(tp):
    assert type(tp) is str
    return tp == NUMERICAL


def len_discretized_values(x, tx, ffactor, maxdev):
    return len(discretized_values(x, tx, ffactor, maxdev))


def discretized_values(x, tx, ffactor, maxdev):
    if numerical(tx) and count_unique(x) > (2 * ffactor * maxdev + 1):
        vmax = ffactor * maxdev
        vmin = -ffactor * maxdev
        return range(vmin, vmax + 1)
    else:
        return sorted(list(set(x)))


def discretized_sequence(x, tx, ffactor, maxdev, norm=True):
    if not norm or (numerical(tx) and count_unique(x) > len_discretized_values(x, tx, ffactor, maxdev)):
        if norm:
            x = (x - np.mean(x)) / np.std(x)
            xf = x[abs(x) < maxdev]
            x = (x - np.mean(xf)) / np.std(xf)
        x = np.round(x * ffactor)
        vmax = ffactor * maxdev
        vmin = -ffactor * maxdev
        x[x > vmax] = vmax
        x[x < vmin] = vmin
    return x


def discretized_sequences(x, y, ffactor=3, maxdev=3):
    return discretized_sequence(x, "Numerical", ffactor, maxdev), discretized_sequence(y, "Numerical", ffactor,
                                                                                       maxdev)


class CDS(Pairwise_Model):
    """
    Conditional Distribution Similarity Statistic

    Measuring the std. of the rescaled values of y (resp. x) after binning in the x (resp. y) direction.
    The lower the std. the more likely the pair to be x->y (resp. y->x).
    Ref : Fonollosa, José AR, "Conditional distribution variability measures for causality detection", 2016.
    """
    def __init__(self, ffactor=2, maxdev=3, minc=12):
        super(CDS, self).__init__()
        self.ffactor = ffactor
        self.maxdev = maxdev
        self.minc = minc

    def predict_proba(self, a, b):
        """ Infer causal relationships between 2 variables x_te and y_te using the CDS statistic

        :param a: Input variable 1
        :param b: Input variable 2
        :return: (Value : 1 if a->b and -1 if b->a)
        :rtype: float
        """
        return self.cds_score(b, a) - self.cds_score(a, b)

    def cds_score(self, x_te, y_te):
        """ Computes the cds statistic from variable 1 to variable 2

        :param x_te: Input, seen as cause
        :param y_te: Input, seen as effect
        :return: CDS statistic between x_te and y_te
        """
        xd, yd = discretized_sequences(x_te,  y_te,  self.ffactor, self.maxdev)
        cx = Counter(xd)
        cy = Counter(yd)
        yrange = sorted(cy.keys())
        ny = len(yrange)
        py = np.array([cy[i] for i in yrange], dtype=float)
        py = py / py.sum()
        pyx = []
        for a in cx.iterkeys():
            if cx[a] > self.minc:
                yx = y_te[xd == a]
                # if not numerical(ty):
                #     cyx = Counter(yx)
                #     pyxa = np.array([cyx[i] for i in yrange], dtype=float)
                #     pyxa.sort()
                if count_unique(y_te) > len_discretized_values(y_te, "Numerical", self.ffactor, self.maxdev):

                    yx = (yx - np.mean(yx)) / np.std(y_te)
                    yx = discretized_sequence(yx, "Numerical", self.ffactor, self.maxdev, norm=False)
                    cyx = Counter(yx.astype(int))
                    pyxa = np.array([cyx[i] for i in discretized_values(y_te, "Numerical", self.ffactor, self.maxdev)],
                                    dtype=float)

                else:
                    print("OK22")
                    cyx = Counter(yx)
                    pyxa = [cyx[i] for i in yrange]
                    pyxax = np.array([0] * (ny - 1) + pyxa + [0] * (ny - 1), dtype=float)
                    xcorr = [sum(py * pyxax[i:i + ny]) for i in range(2 * ny - 1)]
                    imax = xcorr.index(max(xcorr))
                    pyxa = np.array([0] * (2 * ny - 2 - imax) + pyxa + [0] * imax, dtype=float)
                assert pyxa.sum() == cx[a]
                pyxa = pyxa / pyxa.sum()

                pyx.append(pyxa)

        if len(pyx) == 0:
            return 0

        pyx = np.array(pyx)
        pyx = pyx - pyx.mean(axis=0)
        return np.std(pyx)
