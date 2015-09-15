from distutils.command.config import config
import pulp
import numpy
from rlp import *
import cvxopt
import picos
import logging
import abc

log = logging.getLogger(__name__)

# constants
LpMinimize = 1
LpMaximize = -1


class LpSolver():
    """
    Representation of a linear program solver. Intended to be inherited by multiple LP solver implementations.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def solve(c, g, h, a, b):
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

    def solve(self, c, g, h, a, b):
        
        #I prefer to output the scipy matrices 
        log.debug("c: \n" + str(c))
        log.debug("g: \n" + str(g))
        log.debug("h: \n" + str(h))
        log.debug("a: \n" + str(a))
        log.debug("b: \n" + str(b))

        c, g, h, a, b = get_cvxopt_matrices(c, g, h, a, b)


        #solver = self.options.get("cvxopt_solver","conelp")
        solver = "glpk"
        self._result = cvxopt.solvers.lp(c, G=g, h=h, A=a, b=b, solver=solver)
        print(str(self._result["x"]))
        return self._result['x']

    def status(self):
        return self._result.get("status")


class PicosSolver(LpSolver):

    def solve(self, c, g, h, a, b):
        c, g, h, a, b = get_cvxopt_matrices(c, g, h, a, b)

        solver=self.options.get("picos_solver","cvxopt")

        problem = picos.Problem(solver=solver)

        x = problem.add_variable('x', c.size)

        problem.add_constraint(a*x == b)
        problem.add_constraint(g*x <= h)

        problem.minimize(c.T*x)

        self._result = problem
        return x.value

    def status(self):
        return self._result.status

#def get_cvxopt_spmatrix(scipy_sparse_matrix):

#def get_cvxopt_


def get_cvxopt_matrices(c, g, h, a, b):

        a = a if a is None else cvxopt.spmatrix(a.data, a.row.tolist(), a.col.tolist(), size=a.shape)
        g = g if g is None else cvxopt.spmatrix(g.data, g.row.tolist(), g.col.tolist(), size=g.shape)

        b = b if b is None else cvxopt.matrix(b)
        c = cvxopt.matrix(c)
        h = h if h is None else cvxopt.matrix(h)

        return c, g, h, a, b