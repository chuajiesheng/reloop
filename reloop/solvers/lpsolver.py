from distutils.command.config import config
import pulp
import numpy as np
import scipy.sparse as sp
import cvxopt
import picos
import logging
import abc
import reloop.utils.saucy as saucy

log = logging.getLogger(__name__)

# constants
LpMinimize = 1
LpMaximize = -1


class LpSolver():
    """
    Representation of a linear program solver. Intended to be inherited by multiple LP solver implementations.
    """
    __metaclass__ = abc.ABCMeta

    _solver_options = {}
    _lifted_options = {}
    _lifted = False

    @abc.abstractmethod
    def solve(c, g, h, a, b, **kwargs):
        """
        Solves the lp
        :return: The solution of the LP
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def status(self):
        """
        :return: The solution status of the LP.
        """
        raise NotImplementedError()

    def setopts(self, opts):
        #init defaults and provided options
        self._solver_options = {}
        for k, v in opts.items():

            if k.startswith("solver_"):
                self._solver_options[k[7:]] = v
            elif k.startswith("lifted_"):
                self._lifted_options[k[7:]] = v #remarkably, both "lifted_" and "solver_" are 7 letters

        if "lifted" in opts:
            self._lifted = opts["lifted"]


class Pulp(LpSolver):
    """
    LPProblem implementation which uses the LP Solver provided by Pulp
    """
    pass


class LiftedLinear(LpSolver):

    def solve(self):
        pass

    def status(self):
        return "Not Available for LiftedLinearSolver"


class CvxoptSolver(LpSolver):

    def __init__(self, **kwargs):
        #defaults
        self._lifted = False
        #solver defaults
        #default solver is conelp, since glpk requires recompilation of cvxopt
        self._solver_options["solver"] = "conelp"
        #lifting defaults
        self._lifted_options["orbits"] = False
        self._lifted_options["sparse"] = True

        #process user options
        self.setopts(kwargs)

    def solve(self, c, g, h, a, b, **kwargs):

        if kwargs: self.setopts(kwargs)
        log.debug("entering solve() with arguments: \n" + ", ".join([str(u) + "=" + str(v) for u,v in kwargs.items()]))


        if self._lifted:
        #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
        #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
        #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
        #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
        #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
        #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
            Lg, Lh, Lc, La, Lb, compresstime, Bcc = saucy.liftAbc(g, h, c, G=a, h=b, **self._lifted_options)
            c, g, h, a, b = get_cvxopt_matrices(Lc, Lg, Lh, La, Lb)
        else: c, g, h, a, b = get_cvxopt_matrices(c, g, h, a, b)


        self._result = cvxopt.solvers.lp(c, G=g, h=h, A=a, b=b, **self._solver_options)


        try:
            xopt = self._result["x"]
        except:
            xopt = np.array([0])
        else:
            if self._lifted:
                r = sp.csr_matrix(np.array(xopt).ravel())
                xopt = np.array((Bcc * r.T).todense()).ravel()

        return xopt

    def status(self):
        return self._result.get("status")


class PicosSolver(LpSolver):

    def __init__(self, **kwargs):
        #defaults
        self._lifted = False
        #solver defaults
        #default solver is cvxopt since we already have the dependency
        self._solver_options["solver"] = "cvxopt"
        #lifting defaults
        self._lifted_options["orbits"] = False
        self._lifted_options["sparse"] = True

        self.setopts(kwargs)

    def solve(self, c, g, h, a, b, **kwargs):
        if kwargs: self.setopts(kwargs)
        log.debug("entering solve() with settings: \n" + ", ".join([str(u) + "=" + str(v) for u,v in self._solver_options.items()]) + "\n" \
                                                           + ", ".join([str(u) + "=" + str(v) for u,v in self._lifted_options.items()]) )
        problem = picos.Problem(**self._solver_options)

        if self._lifted:
            #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
            #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
            #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
            #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
            #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
            #TODO: refactor lifting code to reflect that g,h are now used for a,b and vice-versa
            Lg, Lh, Lc, La, Lb, compresstime, Bcc = saucy.liftAbc(g, h, c, G=a, h=b, **self._lifted_options)
            c, g, h, a, b = get_cvxopt_matrices(Lc, Lg, Lh, La, Lb)
            print g
        else: c, g, h, a, b = get_cvxopt_matrices(c, g, h, a, b)

        x = problem.add_variable('x', c.size)

        if (a is not None):
            problem.add_constraint(a*x == b)
        if (g is not None):
            problem.add_constraint(g*x <= h)


        problem.set_objective('min', c.T * x)

        self._result = problem.solve()

        try:
            xopt = x.value
        except:
            xopt = None
        else:
            if self._lifted:
                r = sp.csr_matrix(np.array(xopt).ravel())
                xopt = np.array((Bcc * r.T).todense()).ravel()

        return xopt

    def status(self):
        return self._result.status


def get_cvxopt_matrices(c, g, h, a, b):

        a = a if a is None else cvxopt.spmatrix(a.data, a.row.tolist(), a.col.tolist(), size=a.shape)
        g = g if g is None else cvxopt.spmatrix(g.data, g.row.tolist(), g.col.tolist(), size=g.shape)

        b = b if b is None else cvxopt.matrix(b)
        c = cvxopt.matrix(c)
        h = h if h is None else cvxopt.matrix(h)

        return c, g, h, a, b

