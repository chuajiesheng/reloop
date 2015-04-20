import pulp as lp

# constants
LpMinimize = 1
LpMaximize = -1

class LpProblem():

    def __init__(self, name, sense):
        self.name = name
        self.sense = sense

    def solve(self):
        raise NotImplementedError

    def status(self):
        raise NotImplementedError

    def __iadd__(self, other):
        raise NotImplementedError

    def lp_variable(self, name):
        raise NotImplementedError

    def affine_expression(self, x, y):
         raise NotImplementedError


class Pulp(LpProblem):
    def __init__(self, name, sense):
        LpProblem.__init__(self, name, sense)
        self.lpmodel = lp.LpProblem(name, sense)

    def lp_variable(self, name):
        return lp.LpVariable(name)

    def solve(self):
        self.lpmodel.solve()

    def status(self):
        return lp.LpStatus[self.lpmodel.status]

    def __iadd__(self, other):
        if isinstance(other, tuple):
            self.lpmodel += lp.LpConstraint(*other)
        else:
            self.lpmodel += other

        return self

    def affine_expression(self, x, y):
        return lp.LpAffineExpression([(x[i], y[i]) for i in range(len(x))])