# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import unified_planning as up
from unified_planning.model import FNode
from unified_planning.walkers import DagWalker
import pytamer # type: ignore
from fractions import Fraction
from typing import Dict, List


class Converter(DagWalker):
    def __init__(self, env: pytamer.tamer_env,
                 problem: 'up.model.Problem',
                 fluents: Dict['up.model.Fluent', pytamer.tamer_fluent] = {},
                 instances: Dict['up.model.Object', pytamer.tamer_instance] = {},
                 parameters: Dict['up.model.Parameter', pytamer.tamer_param]={}):
        DagWalker.__init__(self)
        self._env = env
        self._fluents = fluents
        self._instances = instances
        self._parameters = parameters
        self._expr_manager = problem.env.expression_manager
        self._objects = {}
        for ut in problem.user_types:
            for obj in problem.objects(ut):
                self._objects[obj.name] = obj

    def convert(self, expression: 'FNode') -> pytamer.tamer_expr:
        """Converts the given expression."""
        return self.walk(expression)

    def convert_back(self, expression: pytamer.tamer_expr) -> 'FNode':
        if pytamer.tamer_expr_is_boolean_constant(self._env, expression) == 1:
            res = self._expr_manager.Bool(pytamer.tamer_expr_get_boolean_constant(self._env, expression) == 1)
        elif pytamer.tamer_expr_is_instance_reference(self._env, expression) == 1:
            i = pytamer.tamer_expr_get_instance(self._env, expression)
            res = self._expr_manager.ObjectExp(self._objects[pytamer.tamer_instance_get_name(i)])
        elif pytamer.tamer_expr_is_integer_constant(self._env, expression) == 1:
            i = pytamer.tamer_expr_get_integer_constant(self._env, expression)
            res = self._expr_manager.Int(i)
        elif pytamer.tamer_expr_is_rational_constant(self._env, expression) == 1:
            n, d = pytamer.tamer_expr_get_rational_constant(self._env, expression)
            res = self._expr_manager.Real(Fraction(n, d))
        else:
            raise NotImplementedError
        return res

    def walk_and(self, expression: 'FNode',
                 args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        if len(args) == 0:
            return pytamer.tamer_expr_make_true(self._env)
        elif len(args) == 1:
            return args[0]
        else:
            res = args[0]
            for i in range(1, len(args)):
                res = pytamer.tamer_expr_make_and(self._env, res, args[i])
            return res

    def walk_or(self, expression: 'FNode',
                args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        if len(args) == 0:
            return pytamer.tamer_expr_make_true(self._env)
        elif len(args) == 1:
            return args[0]
        else:
            res = args[0]
            for i in range(1, len(args)):
                res = pytamer.tamer_expr_make_or(self._env, res, args[i])
            return res

    def walk_not(self, expression: 'FNode',
                 args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 1
        return pytamer.tamer_expr_make_not(self._env, args[0])

    def walk_implies(self, expression: 'FNode',
                     args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 2
        return pytamer.tamer_expr_make_implies(self._env, args[0], args[1])

    def walk_iff(self, expression: 'FNode',
                 args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 2
        return pytamer.tamer_expr_make_iff(self._env, args[0], args[1])

    def walk_fluent_exp(self, expression: 'FNode',
                        args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        fluent = expression.fluent()
        return pytamer.tamer_expr_make_fluent_reference(self._env, self._fluents[fluent], args)

    def walk_param_exp(self, expression: 'FNode',
                       args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 0
        p = expression.parameter()
        return pytamer.tamer_expr_make_parameter_reference(self._env, self._parameters[p])

    def walk_object_exp(self, expression: 'FNode',
                        args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 0
        o = expression.object()
        return pytamer.tamer_expr_make_instance_reference(self._env, self._instances[o])

    def walk_bool_constant(self, expression: 'FNode',
                           args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 0
        if expression.is_true():
            return pytamer.tamer_expr_make_true(self._env)
        else:
            return pytamer.tamer_expr_make_false(self._env)

    def walk_real_constant(self, expression: 'FNode',
                           args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 0
        n = expression.constant_value().numerator
        d = expression.constant_value().denominator
        return pytamer.tamer_expr_make_rational_constant(self._env, n, d)

    def walk_int_constant(self, expression: 'FNode',
                          args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 0
        return pytamer.tamer_expr_make_integer_constant(self._env, expression.constant_value())

    def walk_plus(self, expression: 'FNode',
                  args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 2
        return pytamer.tamer_expr_make_plus(self._env, args[0], args[1])

    def walk_minus(self, expression: 'FNode',
                   args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 2
        return pytamer.tamer_expr_make_minus(self._env, args[0], args[1])

    def walk_times(self, expression: 'FNode',
                   args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 2
        return pytamer.tamer_expr_make_times(self._env, args[0], args[1])

    def walk_div(self, expression: 'FNode',
                 args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 2
        return pytamer.tamer_expr_make_div(self._env, args[0], args[1])

    def walk_le(self, expression: 'FNode',
                args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 2
        return pytamer.tamer_expr_make_le(self._env, args[0], args[1])

    def walk_lt(self, expression: 'FNode',
                args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 2
        return pytamer.tamer_expr_make_lt(self._env, args[0], args[1])

    def walk_equals(self, expression: 'FNode',
                    args: List[pytamer.tamer_expr]) -> pytamer.tamer_expr:
        assert len(args) == 2
        return pytamer.tamer_expr_make_equals(self._env, args[0], args[1])
