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
        c, g, h, a, b = get_cvxopt_matrices(c, g, h, a, b)

        print("START MATRICES")
        print(c)
        print(g)
        print(h)
        print(a)
        print(b)
        print("END MATRICES")


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


def get_cvxopt_matrices(c, g, h, a, b):

        a = cvxopt.spmatrix(a.data, a.row.tolist(), a.col.tolist(), size=a.shape)
        g = cvxopt.spmatrix(g.data, g.row.tolist(), g.col.tolist(), size=g.shape)

        b = cvxopt.matrix(b)
        c = cvxopt.matrix(c)
        h = cvxopt.matrix(h)

        return c, g, h, a, b