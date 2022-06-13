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


import sys
import warnings
import unified_planning as up
import pytamer # type: ignore
import unified_planning.engines
import unified_planning.engines.mixins
from unified_planning.model import ProblemKind
from unified_planning.engines import PlanGenerationResultStatus, ValidationResult, ValidationResultStatus, Credits
from up_tamer.converter import Converter
from fractions import Fraction
from typing import IO, Callable, Optional, Dict, List, Tuple, Union, cast



credits = Credits('Tamer',
                  'FBK Tamer Development Team',
                  'tamer@fbk.eu',
                  'https://tamer.fbk.eu',
                  'Free for Educational Use',
                  'Tamer offers the capability to generate a plan for classical, numerical and temporal problems.\nFor those kind of problems tamer also offers the possibility of validating a submitted plan.',
                  'Tamer offers the capability to generate a plan for classical, numerical and temporal problems.\nFor those kind of problems tamer also offers the possibility of validating a submitted plan.\nYou can find all the related publications here: https://tamer.fbk.eu/publications/'
                )

class TState(up.model.State):
    def __init__(self, ts: pytamer.tamer_state,
                 interpretation: pytamer.tamer_interpretation,
                 converter: Converter):
        self._ts = ts
        self._interpretation = interpretation
        self._converter = converter

    def get_value(self, f: 'up.model.FNode') -> 'up.model.FNode':
        cf = self._converter.convert(f)
        r = pytamer.tamer_state_get_value(self._ts, self._interpretation, cf)
        cr = self._converter.convert_back(r)
        return cr


class EngineImpl(up.engines.Engine,
                 up.engines.mixins.OneshotPlannerMixin,
                 up.engines.mixins.PlanValidatorMixin):

    def __init__(self, weight: Optional[float] = None,
                 heuristic: Optional[str] = None, **options):
        self._env = pytamer.tamer_env_new()
        if not weight is None:
            pytamer.tamer_env_set_float_option(self._env, 'weight', weight)
        self._heuristic = heuristic
        if len(options) > 0:
            raise up.exceptions.UPUsageError('Custom options not supported!')
        self._bool_type = pytamer.tamer_boolean_type(self._env)
        self._tamer_start = \
            pytamer.tamer_expr_make_point_interval(self._env,
                                                   pytamer.tamer_expr_make_start_anchor(self._env))
        self._tamer_end = \
            pytamer.tamer_expr_make_point_interval(self._env,
                                                   pytamer.tamer_expr_make_end_anchor(self._env))

    @property
    def name(self) -> str:
        return 'Tamer'

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class('ACTION_BASED') # type: ignore
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
        supported_kind.set_simulated_entities('SIMULATED_EFFECTS') # type: ignore
        return supported_kind

    @staticmethod
    def supports(problem_kind: 'up.model.ProblemKind') -> bool:
        return problem_kind <= EngineImpl.supported_kind()

    @staticmethod
    def satisfies(optimality_guarantee: up.engines.OptimalityGuarantee) -> bool:
        return False

    @staticmethod
    def get_credits(**kwargs) -> Optional[up.engines.Credits]:
        return credits

    def validate(self, problem: 'up.model.AbstractProblem', plan: 'up.plans.Plan') -> 'up.engines.results.ValidationResult':
        if not self.supports(problem.kind):
            raise up.exceptions.UPUsageError('Tamer cannot validate this kind of problem!')
        assert isinstance(problem, up.model.Problem)
        if plan is None:
            raise up.exceptions.UPUsageError('Tamer cannot validate an empty plan!')
        tproblem = self._convert_problem(problem)
        tplan = self._convert_plan(tproblem, plan)
        value = pytamer.tamer_ttplan_validate(tproblem, tplan) == 1
        return ValidationResult(ValidationResultStatus.VALID if value else ValidationResultStatus.INVALID, self.name, [])

    def solve(self, problem: 'up.model.AbstractProblem',
              callback: Optional[Callable[['up.engines.PlanGenerationResult'], None]] = None,
              timeout: Optional[float] = None,
              output_stream: Optional[IO[str]] = None) -> 'up.engines.results.PlanGenerationResult':
        if not self.supports(problem.kind):
            raise up.exceptions.UPUsageError('Tamer cannot solve this kind of problem!')
        assert isinstance(problem, up.model.Problem)
        if timeout is not None:
            warnings.warn('Tamer does not support timeout.', UserWarning)
        if output_stream is not None:
            warnings.warn('Tamer does not support output stream.', UserWarning)
        tproblem = self._convert_problem(problem)
        if problem.kind.has_continuous_time(): # type: ignore
            if self._heuristic is not None:
                pytamer.tamer_env_set_vector_string_option(self._env, 'ftp-heuristic', [self._heuristic])
            ttplan = pytamer.tamer_do_ftp_planning(tproblem)
            if pytamer.tamer_ttplan_is_error(ttplan) == 1:
                ttplan = None
        else:
            if self._heuristic is not None:
                pytamer.tamer_env_set_string_option(self._env, 'tsimple-heuristic', self._heuristic)
            ttplan = self._solve_classical_problem(tproblem)
        plan = self._to_up_plan(problem, ttplan)
        return up.engines.PlanGenerationResult(PlanGenerationResultStatus.UNSOLVABLE_PROVEN if plan is None else PlanGenerationResultStatus.SOLVED_SATISFICING, plan, self.name)

    def _convert_type(self, typename: 'up.model.Type',
                      user_types_map: Dict['up.model.Type', pytamer.tamer_type]) -> pytamer.tamer_type:
        if typename.is_bool_type():
            ttype = self._bool_type
        elif typename.is_user_type():
            ttype = user_types_map[typename]
        elif typename.is_int_type():
            typename = cast(up.model.types._IntType, typename)
            ilb = typename.lower_bound
            iub = typename.upper_bound
            if ilb is None and iub is None:
                ttype = pytamer.tamer_integer_type(self._env)
            elif ilb is None:
                ttype = pytamer.tamer_integer_type_lb(self._env, ilb)
            elif iub is None:
                ttype = pytamer.tamer_integer_type_ub(self._env, iub)
            else:
                ttype = pytamer.tamer_integer_type_lub(self._env, ilb, iub)
        elif typename.is_real_type():
            typename = cast(up.model.types._RealType, typename)
            flb = typename.lower_bound
            fub = typename.upper_bound
            if flb is None and fub is None:
                ttype = pytamer.tamer_rational_type(self._env)
            elif flb is None:
                ttype = pytamer.tamer_rational_type_lb(self._env, flb)
            elif fub is None:
                ttype = pytamer.tamer_rational_type_ub(self._env, fub)
            else:
                ttype = pytamer.tamer_rational_type_lub(self._env, flb, fub)
        else:
            raise NotImplementedError
        return ttype

    def _convert_fluent(self, fluent: 'up.model.Fluent',
                        user_types_map: Dict['up.model.Type',
                                             pytamer.tamer_fluent]) -> pytamer.tamer_fluent:
        typename = fluent.type
        ttype = self._convert_type(typename, user_types_map)
        params = []
        for param in fluent.signature:
            ptype = self._convert_type(param.type, user_types_map)
            p = pytamer.tamer_parameter_new(param.name, ptype)
            params.append(p)
        return pytamer.tamer_fluent_new(self._env, fluent.name, ttype, [], params)

    def _convert_timing(self, timing: 'up.model.Timing') -> pytamer.tamer_expr:
        k = timing.delay
        if isinstance(k, int):
            c = pytamer.tamer_expr_make_integer_constant(self._env, k)
        elif isinstance(k, float):
            k = Fraction(k)
            c = pytamer.tamer_expr_make_rational_constant(self._env, k.numerator, k.denominator)
        elif isinstance(k, Fraction):
            c = pytamer.tamer_expr_make_rational_constant(self._env, k.numerator, k.denominator)
        else:
            raise NotImplementedError
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

    def _convert_interval(self, interval: 'up.model.TimeInterval') -> pytamer.tamer_expr:
        if interval.lower == interval.upper:
            return self._convert_timing(interval.lower)
        lower = pytamer.tamer_expr_get_child(self._convert_timing(interval.lower), 0)
        upper = pytamer.tamer_expr_get_child(self._convert_timing(interval.upper), 0)
        if interval.is_left_open() and interval.is_right_open():
            return pytamer.tamer_expr_make_open_interval(self._env, lower, upper)
        elif interval.is_left_open():
            return pytamer.tamer_expr_make_left_open_interval(self._env, lower, upper)
        elif interval.is_right_open():
            return pytamer.tamer_expr_make_right_open_interval(self._env, lower, upper)
        else:
            return pytamer.tamer_expr_make_closed_interval(self._env, lower, upper)

    def _convert_duration(self, converter: Converter,
                          duration: 'up.model.DurationInterval') -> pytamer.tamer_expr:
        d = pytamer.tamer_expr_make_duration_anchor(self._env)
        lower = converter.convert(duration.lower)
        upper = converter.convert(duration.upper)
        if duration.lower == duration.upper:
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

    def _convert_simulated_effect(self, converter: Converter, problem: 'up.model.Problem',
                                  action: 'up.model.Action', timing: 'up.model.Timing',
                                  sim_eff: 'up.model.SimulatedEffect') -> pytamer.tamer_simulated_effect:
        fluents = [converter.convert(x) for x in sim_eff.fluents]
        def f(ts: pytamer.tamer_classical_state,
              interpretation: pytamer.tamer_interpretation,
              actual_params: pytamer.tamer_vector_expr,
              res: pytamer.tamer_vector_expr):
            s = TState(ts, interpretation, converter)
            actual_params_dict = {}
            for i, p in enumerate(action.parameters):
                tvalue = pytamer.tamer_vector_get_expr(actual_params, i)
                actual_params_dict[p] = converter.convert_back(tvalue)
            vec = sim_eff.function(problem, s, actual_params_dict)
            for x in vec:
                pytamer.tamer_vector_add_expr(res, converter.convert(x))
        return pytamer.tamer_simulated_effect_new(self._convert_timing(timing), fluents, f);

    def _convert_action(self, problem: 'up.model.Problem', action: 'up.model.Action',
                        fluents_map: Dict['up.model.Fluent', pytamer.tamer_fluent],
                        user_types_map: Dict['up.model.Type', pytamer.tamer_type],
                        instances_map: Dict['up.model.Object', pytamer.tamer_instance]) -> pytamer.tamer_action:
        params = []
        params_map = {}
        for p in action.parameters:
            ptype = self._convert_type(p.type, user_types_map)
            new_p = pytamer.tamer_parameter_new(p.name, ptype)
            params.append(new_p)
            params_map[p] = new_p
        expressions = []
        simulated_effects = []
        converter = Converter(self._env, problem, fluents_map, instances_map, params_map)
        if isinstance(action, up.model.InstantaneousAction):
            for c in action.preconditions:
                expr = pytamer.tamer_expr_make_temporal_expression(self._env, self._tamer_start,
                                                                   converter.convert(c))
                expressions.append(expr)
            for e in action.effects:
                assert not e.is_conditional() and e.is_assignment()
                ass = pytamer.tamer_expr_make_assign(self._env, converter.convert(e.fluent), converter.convert(e.value))
                expr = pytamer.tamer_expr_make_temporal_expression(self._env, self._tamer_start, ass)
                expressions.append(expr)
            expr = pytamer.tamer_expr_make_assign(self._env, pytamer.tamer_expr_make_duration_anchor(self._env),
                                                  pytamer.tamer_expr_make_integer_constant(self._env, 1))
            expressions.append(expr)
            se = action.simulated_effect
            if se is not None:
                simulated_effects.append(self._convert_simulated_effect(converter, problem, action,
                                                                        up.model.StartTiming(), se))
        elif isinstance(action, up.model.DurativeAction):
            for i, lc in action.conditions.items():
                for c in lc:
                    expr = pytamer.tamer_expr_make_temporal_expression(self._env,
                                                                       self._convert_interval(i),
                                                                       converter.convert(c))
                    expressions.append(expr)
            for t, le in action.effects.items():
                for e in le:
                    assert not e.is_conditional() and e.is_assignment()
                    ass = pytamer.tamer_expr_make_assign(self._env, converter.convert(e.fluent),
                                                         converter.convert(e.value))
                    expr = pytamer.tamer_expr_make_temporal_expression(self._env,
                                                                       self._convert_timing(t),
                                                                       ass)
                    expressions.append(expr)
            for t, se in action.simulated_effects.items():
                simulated_effects.append(self._convert_simulated_effect(converter, problem, action, t, se))
            expressions.append(self._convert_duration(converter, action.duration))
        else:
            raise NotImplementedError
        return pytamer.tamer_action_new(self._env, action.name, [], params, expressions, simulated_effects)

    def _convert_problem(self, problem: 'up.model.Problem') -> pytamer.tamer_problem:
        user_types = []
        user_types_map = {}
        instances = []
        instances_map = {}
        for ut in problem.user_types:
            name = cast(up.model.types._UserType, ut).name
            new_ut = pytamer.tamer_user_type_new(self._env, name)
            user_types.append(new_ut)
            user_types_map[ut] = new_ut
            for obj in problem.objects(ut):
                new_obj = pytamer.tamer_instance_new(self._env, obj.name, user_types_map[ut])
                instances.append(new_obj)
                instances_map[obj] = new_obj

        fluents = []
        fluents_map = {}
        for f in problem.fluents:
            new_f = self._convert_fluent(f, user_types_map)
            fluents.append(new_f)
            fluents_map[f] = new_f

        actions = []
        for a in problem.actions:
            new_a = self._convert_action(problem, a, fluents_map, user_types_map, instances_map)
            actions.append(new_a)

        expressions = []
        converter = Converter(self._env, problem, fluents_map, instances_map)
        for k, v in problem.initial_values.items():
            ass = pytamer.tamer_expr_make_assign(self._env, converter.convert(k), converter.convert(v))
            expr = pytamer.tamer_expr_make_temporal_expression(self._env, self._tamer_start, ass)
            expressions.append(expr)
        for g in problem.goals:
            expr = pytamer.tamer_expr_make_temporal_expression(self._env, self._tamer_end,
                                                               converter.convert(g))
            expressions.append(expr)
        for t, le in problem.timed_effects.items():
            t = self._convert_timing(t)
            for e in le:
                assert not e.is_conditional() and e.is_assignment()
                ass = pytamer.tamer_expr_make_assign(self._env, converter.convert(e.fluent),
                                                     converter.convert(e.value))
                expr = pytamer.tamer_expr_make_temporal_expression(self._env, t, ass)
                expressions.append(expr)
        for i, l in problem.timed_goals.items():
            i = self._convert_interval(i)
            for g in l:
                expr = pytamer.tamer_expr_make_temporal_expression(self._env, i,
                                                                   converter.convert(g))
                expressions.append(expr)

        return pytamer.tamer_problem_new(self._env, actions, fluents, [], instances, user_types, expressions)

    def _to_up_plan(self, problem: 'up.model.Problem',
                    ttplan: Optional[pytamer.tamer_ttplan]) -> Optional['up.plans.Plan']:
        if ttplan is None:
            return None
        converter = Converter(self._env, problem)
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
                params.append(converter.convert_back(p))
            actions.append((start, up.plans.ActionInstance(action, tuple(params)), duration))
        if problem.kind.has_continuous_time(): # type: ignore
            return up.plans.TimeTriggeredPlan(actions, problem.env)
        else:
            return up.plans.SequentialPlan([a[1] for a in actions], problem.env)

    def _solve_classical_problem(self, tproblem: pytamer.tamer_problem) -> Optional[pytamer.tamer_ttplan]:
        potplan = pytamer.tamer_do_tsimple_planning(tproblem)
        if pytamer.tamer_potplan_is_error(potplan) == 1:
            return None
        ttplan = pytamer.tamer_ttplan_from_potplan(potplan)
        return ttplan

    def _convert_plan(self, tproblem: pytamer.tamer_problem, plan: 'up.plans.Plan') -> pytamer.tamer_ttplan:
        actions_map = {}
        for a in pytamer.tamer_problem_get_actions(tproblem):
            actions_map[pytamer.tamer_action_get_name(a)] = a
        instances_map = {}
        for i in pytamer.tamer_problem_get_instances(tproblem):
            instances_map[pytamer.tamer_instance_get_name(i)] = i
        ttplan = pytamer.tamer_ttplan_new(self._env)
        steps: List[Tuple[Fraction, 'up.plans.ActionInstance', Optional[Fraction]]] = []
        if isinstance(plan, up.plans.SequentialPlan):
            steps = [(Fraction(i*2), a, Fraction(1)) for i, a in enumerate(plan.actions)]
        elif isinstance(plan, up.plans.TimeTriggeredPlan):
            steps = plan.timed_actions
        else:
            raise NotImplementedError
        for start, ai, duration in steps:
            action = actions_map[ai.action.name]
            params = []
            for p in ai.actual_parameters:
                if p.is_object_exp():
                    i = instances_map[p.object().name]
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
                    raise NotImplementedError
            step = pytamer.tamer_ttplan_step_new(str(start), action, params, str(duration), \
                                                 pytamer.tamer_expr_make_true(self._env))
            pytamer.tamer_ttplan_add_step(ttplan, step)
        return ttplan
