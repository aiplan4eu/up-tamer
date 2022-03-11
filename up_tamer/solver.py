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

import unified_planning as up
import pytamer # type: ignore
from unified_planning.model import ProblemKind
from up_tamer.converter import Converter
from fractions import Fraction
from typing import Optional, Dict, List, Tuple


class SolverImpl(up.solvers.Solver):
    def __init__(self, weight: Optional[float] = None,
                 heuristic: Optional[str] = None, **options):
        self._env = pytamer.tamer_env_new()
        if not weight is None:
            pytamer.tamer_env_set_float_option(self._env, 'weight', weight)
        self._heuristic = heuristic
        if len(options) > 0:
            raise
        self._bool_type = pytamer.tamer_boolean_type(self._env)
        self._tamer_start = \
            pytamer.tamer_expr_make_point_interval(self._env,
                                                   pytamer.tamer_expr_make_start_anchor(self._env))
        self._tamer_end = \
            pytamer.tamer_expr_make_point_interval(self._env,
                                                   pytamer.tamer_expr_make_end_anchor(self._env))

    @staticmethod
    def name() -> str:
        return 'Tamer'

    def _convert_type(self, typename: 'up.model.Type',
                      user_types_map: Dict['up.model.Type', pytamer.tamer_type]) -> pytamer.tamer_type:
        if typename.is_bool_type():
            ttype = self._bool_type
        elif typename.is_user_type():
            ttype = user_types_map[typename]
        elif typename.is_int_type():
            lb = typename.lower_bound() # type: ignore
            ub = typename.upper_bound() # type: ignore
            if lb is None and ub is None:
                ttype = pytamer.tamer_integer_type(self._env)
            elif lb is None:
                ttype = pytamer.tamer_integer_type_lb(self._env, lb)
            elif ub is None:
                ttype = pytamer.tamer_integer_type_ub(self._env, ub)
            else:
                ttype = pytamer.tamer_integer_type_lub(self._env, lb, ub)
        elif typename.is_real_type():
            lb = typename.lower_bound() # type: ignore
            ub = typename.upper_bound() # type: ignore
            if lb is None and ub is None:
                ttype = pytamer.tamer_rational_type(self._env)
            elif lb is None:
                ttype = pytamer.tamer_rational_type_lb(self._env, lb)
            elif ub is None:
                ttype = pytamer.tamer_rational_type_ub(self._env, ub)
            else:
                ttype = pytamer.tamer_rational_type_lub(self._env, lb, ub)
        else:
            assert False
        return ttype

    def _convert_fluent(self, fluent: 'up.model.Fluent',
                        user_types_map: Dict['up.model.Type',
                                             pytamer.tamer_fluent]) -> pytamer.tamer_fluent:
        typename = fluent.type()
        ttype = self._convert_type(typename, user_types_map)
        params = []
        for param in fluent.signature():
            ptype = self._convert_type(param.type(), user_types_map)
            p = pytamer.tamer_parameter_new(param.name(), ptype)
            params.append(p)
        return pytamer.tamer_fluent_new(self._env, fluent.name(), ttype, [], params)

    def _convert_timing(self, timing: 'up.model.Timing') -> pytamer.tamer_expr:
        k = timing.delay()
        if isinstance(k, int):
            c = pytamer.tamer_expr_make_integer_constant(self._env, k)
        elif isinstance(k, float):
            k = Fraction(k)
            c = pytamer.tamer_expr_make_rational_constant(self._env, k.numerator, k.denominator)
        elif isinstance(k, Fraction):
            c = pytamer.tamer_expr_make_rational_constant(self._env, k.numerator, k.denominator)
        else:
            raise
        if timing.is_from_start():
            if k == 0:
                return self._tamer_start
            else:
                s = pytamer.tamer_expr_make_start_anchor(self._env)
                r = pytamer.tamer_expr_make_plus(self._env, s, c)
                return pytamer.tamer_expr_make_point_interval(self._env, r)
        elif timing.is_from_end():
            if k == 0:
                return self._tamer_end
            else:
                s = pytamer.tamer_expr_make_end_anchor(self._env)
                r = pytamer.tamer_expr_make_minus(self._env, s, c)
                return pytamer.tamer_expr_make_point_interval(self._env, r)
        else:
            return pytamer.tamer_expr_make_point_interval(self._env, c)

    def _convert_interval(self, interval: 'up.model.Interval') -> pytamer.tamer_expr:
        if interval.lower() == interval.upper():
            return self._convert_timing(interval.lower())
        lower = pytamer.tamer_expr_get_child(self._convert_timing(interval.lower()), 0)
        upper = pytamer.tamer_expr_get_child(self._convert_timing(interval.upper()), 0)
        if interval.is_left_open() and interval.is_right_open():
            return pytamer.tamer_expr_make_open_interval(self._env, lower, upper)
        elif interval.is_left_open():
            return pytamer.tamer_expr_make_left_open_interval(self._env, lower, upper)
        elif interval.is_right_open():
            return pytamer.tamer_expr_make_right_open_interval(self._env, lower, upper)
        else:
            return pytamer.tamer_expr_make_closed_interval(self._env, lower, upper)

    def _convert_duration(self, converter: Converter,
                          duration: 'up.model.IntervalDuration') -> pytamer.tamer_expr:
        d = pytamer.tamer_expr_make_duration_anchor(self._env)
        lower = converter.convert(duration.lower())
        upper = converter.convert(duration.upper())
        if duration.lower() == duration.upper():
            return pytamer.tamer_expr_make_equals(self._env, d, lower)
        if duration.is_left_open():
            l = pytamer.tamer_expr_make_gt(self._env, d, lower)
        else:
            l = pytamer.tamer_expr_make_ge(self._env, d, lower)
        if duration.is_right_open():
            u = pytamer.tamer_expr_make_lt(self._env, d, upper)
        else:
            u = pytamer.tamer_expr_make_le(self._env, d, upper)
        return pytamer.tamer_expr_make_and(self._env, l, u)

    def _convert_action(self, action: 'up.model.Action',
                        fluents_map: Dict['up.model.Fluent', pytamer.tamer_fluent],
                        user_types_map: Dict['up.model.Type', pytamer.tamer_type],
                        instances_map: Dict['up.model.Object', pytamer.tamer_instance]) -> pytamer.tamer_action:
        params = []
        params_map = {}
        for p in action.parameters():
            ptype = self._convert_type(p.type(), user_types_map)
            new_p = pytamer.tamer_parameter_new(p.name(), ptype)
            params.append(new_p)
            params_map[p] = new_p
        expressions = []
        converter = Converter(self._env, fluents_map, instances_map, params_map)
        if isinstance(action, up.model.InstantaneousAction):
            for c in action.preconditions():
                expr = pytamer.tamer_expr_make_temporal_expression(self._env, self._tamer_start,
                                                                   converter.convert(c))
                expressions.append(expr)
            for e in action.effects():
                assert not e.is_conditional() and e.is_assignment()
                ass = pytamer.tamer_expr_make_assign(self._env, converter.convert(e.fluent()), converter.convert(e.value()))
                expr = pytamer.tamer_expr_make_temporal_expression(self._env, self._tamer_start, ass)
                expressions.append(expr)
            expr = pytamer.tamer_expr_make_assign(self._env, pytamer.tamer_expr_make_duration_anchor(self._env),
                                                  pytamer.tamer_expr_make_integer_constant(self._env, 1))
            expressions.append(expr)
        elif isinstance(action, up.model.DurativeAction):
            for i, l in action.conditions().items():
                for c in l:
                    expr = pytamer.tamer_expr_make_temporal_expression(self._env,
                                                                       self._convert_interval(i),
                                                                       converter.convert(c))
                    expressions.append(expr)
            for t, l in action.effects().items():
                for e in l:
                    assert not e.is_conditional() and e.is_assignment()
                    ass = pytamer.tamer_expr_make_assign(self._env, converter.convert(e.fluent()),
                                                         converter.convert(e.value()))
                    expr = pytamer.tamer_expr_make_temporal_expression(self._env,
                                                                       self._convert_timing(t),
                                                                       ass)
                    expressions.append(expr)
            expressions.append(self._convert_duration(converter, action.duration()))
        else:
            raise
        return pytamer.tamer_action_new(self._env, action.name, [], params, expressions)

    def _convert_problem(self, problem: 'up.model.Problem') -> pytamer.tamer_problem:
        user_types = []
        user_types_map = {}
        instances = []
        instances_map = {}
        for ut in problem.user_types():
            name = ut.name() # type: ignore
            new_ut = pytamer.tamer_user_type_new(self._env, name)
            user_types.append(new_ut)
            user_types_map[ut] = new_ut
            for obj in problem.objects(ut):
                new_obj = pytamer.tamer_instance_new(self._env, obj.name(), user_types_map[ut])
                instances.append(new_obj)
                instances_map[obj] = new_obj

        fluents = []
        fluents_map = {}
        for f in problem.fluents():
            new_f = self._convert_fluent(f, user_types_map)
            fluents.append(new_f)
            fluents_map[f] = new_f

        actions = []
        for a in problem.actions():
            new_a = self._convert_action(a, fluents_map, user_types_map, instances_map)
            actions.append(new_a)

        expressions = []
        converter = Converter(self._env, fluents_map, instances_map)
        for k, v in problem.initial_values().items():
            ass = pytamer.tamer_expr_make_assign(self._env, converter.convert(k), converter.convert(v))
            expr = pytamer.tamer_expr_make_temporal_expression(self._env, self._tamer_start, ass)
            expressions.append(expr)
        for g in problem.goals():
            expr = pytamer.tamer_expr_make_temporal_expression(self._env, self._tamer_end,
                                                               converter.convert(g))
            expressions.append(expr)
        for t, le in problem.timed_effects().items():
            t = self._convert_timing(t)
            for e in le:
                assert not e.is_conditional() and e.is_assignment()
                ass = pytamer.tamer_expr_make_assign(self._env, converter.convert(e.fluent()),
                                                     converter.convert(e.value()))
                expr = pytamer.tamer_expr_make_temporal_expression(self._env, t, ass)
                expressions.append(expr)
        for i, l in problem.timed_goals().items():
            i = self._convert_interval(i)
            for g in l:
                expr = pytamer.tamer_expr_make_temporal_expression(self._env, i,
                                                                   converter.convert(g))
                expressions.append(expr)

        return pytamer.tamer_problem_new(self._env, actions, fluents, [], instances, user_types, expressions)

    def _to_up_plan(self, problem: 'up.model.Problem',
                     ttplan: Optional[pytamer.tamer_ttplan]) -> Optional['up.plan.Plan']:
        if ttplan is None:
            return None
        expr_manager = problem.env.expression_manager
        objects = {}
        for ut in problem.user_types():
            for obj in problem.objects(ut):
                objects[obj.name()] = obj
        actions = []
        for s in pytamer.tamer_ttplan_get_steps(ttplan):
            taction = pytamer.tamer_ttplan_step_get_action(s)
            start = Fraction(pytamer.tamer_ttplan_step_get_start_time(s))
            duration = None
            name = pytamer.tamer_action_get_name(taction)
            action = problem.action(name)
            if isinstance(action, up.model.DurativeAction):
                duration = Fraction(pytamer.tamer_ttplan_step_get_duration(s))
            params = []
            for p in pytamer.tamer_ttplan_step_get_parameters(s):
                if pytamer.tamer_expr_is_boolean_constant(self._env, p) == 1:
                    new_p = expr_manager.Bool(pytamer.tamer_expr_get_boolean_constant(self._env, p) == 1)
                elif pytamer.tamer_expr_is_instance_reference(self._env, p) == 1:
                    i = pytamer.tamer_expr_get_instance(self._env, p)
                    new_p = expr_manager.ObjectExp(objects[pytamer.tamer_instance_get_name(i)])
                elif pytamer.tamer_expr_is_integer_constant(self._env, p) == 1:
                    i = pytamer.tamer_expr_get_integer_constant(self._env, p)
                    new_p = expr_manager.Int(i)
                elif pytamer.tamer_expr_is_rational_constant(self._env, p) == 1:
                    n, d = pytamer.tamer_expr_get_rational_constant(self._env, p)
                    new_p = expr_manager.Real(Fraction(n, d))
                else:
                    raise
                params.append(new_p)
            actions.append((start, up.plan.ActionInstance(action, tuple(params)), duration))
        if problem.kind().has_continuous_time(): # type: ignore
            return up.plan.TimeTriggeredPlan(actions)
        else:
            return up.plan.SequentialPlan([a[1] for a in actions])

    def _solve_classical_problem(self, tproblem: pytamer.tamer_problem) -> Optional[pytamer.tamer_ttplan]:
        potplan = pytamer.tamer_do_tsimple_planning(tproblem)
        if pytamer.tamer_potplan_is_error(potplan) == 1:
            return None
        ttplan = pytamer.tamer_ttplan_from_potplan(potplan)
        return ttplan

    def solve(self, problem: 'up.model.Problem') -> Optional['up.plan.Plan']:
        assert self.supports(problem.kind())
        tproblem = self._convert_problem(problem)
        if problem.kind().has_continuous_time(): # type: ignore
            if self._heuristic is not None:
                pytamer.tamer_env_set_string_option(self._env, 'ftp-heuristic', self._heuristic)
            ttplan = pytamer.tamer_do_ftp_planning(tproblem)
        else:
            if self._heuristic is not None:
                pytamer.tamer_env_set_string_option(self._env, 'tsimple-heuristic', self._heuristic)
            ttplan = self._solve_classical_problem(tproblem)
        return self._to_up_plan(problem, ttplan)

    def _convert_plan(self, tproblem: pytamer.tamer_problem, plan: 'up.plan.Plan') -> pytamer.tamer_ttplan:
        actions_map = {}
        for a in pytamer.tamer_problem_get_actions(tproblem):
            actions_map[pytamer.tamer_action_get_name(a)] = a
        instances_map = {}
        for i in pytamer.tamer_problem_get_instances(tproblem):
            instances_map[pytamer.tamer_instance_get_name(i)] = i
        ttplan = pytamer.tamer_ttplan_new(self._env)
        steps: List[Tuple[Fraction, 'up.plan.ActionInstance', Optional[Fraction]]] = []
        if isinstance(plan, up.plan.SequentialPlan):
            steps = [(Fraction(i*2), a, Fraction(1)) for i, a in enumerate(plan.actions())]
        elif isinstance(plan, up.plan.TimeTriggeredPlan):
            steps = plan.actions()
        else:
            raise
        for start, ai, duration in steps:
            action = actions_map[ai.action().name]
            params = []
            for p in ai.actual_parameters():
                if p.is_object_exp():
                    i = instances_map[p.object().name()]
                    params.append(pytamer.tamer_expr_make_instance_reference(self._env, i))
                elif p.is_true():
                    params.append(pytamer.tamer_expr_make_true(self._env))
                elif p.is_false():
                    params.append(pytamer.tamer_expr_make_false(self._env))
                elif p.is_int_constant():
                    params.append(pytamer.tamer_expr_make_integer_constant(self._env, p.constant_value()))
                elif p.is_real_constant():
                    f = p.constant_value()
                    n = f.numerator
                    d = f.denominator
                    params.append(pytamer.tamer_expr_make_rational_constant(self._env, n, d))
                else:
                    raise
            step = pytamer.tamer_ttplan_step_new(str(start), action, params, str(duration), \
                                                 pytamer.tamer_expr_make_true(self._env))
            pytamer.tamer_ttplan_add_step(ttplan, step)
        return ttplan


    def validate(self, problem: 'up.model.Problem', plan: 'up.plan.Plan') -> bool:
        assert self.supports(problem.kind())
        tproblem = self._convert_problem(problem)
        tplan = self._convert_plan(tproblem, plan)
        return pytamer.tamer_ttplan_validate(tproblem, tplan) == 1

    @staticmethod
    def supports(problem_kind: 'ProblemKind') -> bool:
        supported_kind = ProblemKind()
        supported_kind.set_time('CONTINUOUS_TIME') # type: ignore
        supported_kind.set_time('INTERMEDIATE_CONDITIONS_AND_EFFECTS') # type: ignore
        supported_kind.set_time('TIMED_EFFECT') # type: ignore
        supported_kind.set_time('TIMED_GOALS') # type: ignore
        supported_kind.set_time('DURATION_INEQUALITIES') # type: ignore
        supported_kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
        supported_kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore
        supported_kind.set_typing('FLAT_TYPING') # type: ignore
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('EQUALITY') # type: ignore
        supported_kind.set_fluents_type('NUMERIC_FLUENTS') # type: ignore
        supported_kind.set_fluents_type('OBJECT_FLUENTS') # type: ignore
        return problem_kind <= supported_kind

    @staticmethod
    def is_oneshot_planner() -> bool:
        return True

    @staticmethod
    def is_plan_validator() -> bool:
        return True

    def destroy(self):
        pass
