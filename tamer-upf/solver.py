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

import upf
import pytamer
from upf_tamer.converter import Converter


class SolverImpl(upf.Solver):
    def __init__(self):
        self.env = pytamer.tamer_env_new()
        self.bool_type = pytamer.tamer_boolean_type(self.env)
        self.tamer_start = \
            pytamer.tamer_expr_make_point_interval(self.env,
                                                   pytamer.tamer_expr_make_start_anchor(self.env))
        self.tamer_end = \
            pytamer.tamer_expr_make_point_interval(self.env,
                                                   pytamer.tamer_expr_make_end_anchor(self.env))

    def _convert_fluent(self, fluent, user_types_map):
        name = fluent.name()
        typename = fluent.type()
        if typename.is_bool_type():
            ttype = self.bool_type
        elif typename.is_user_type():
            ttype = user_types_map[typename]
        else:
            raise
        params = []
        i = 0
        for t in fluent.signature():
            if t.is_bool_type():
                ptype = self.bool_type
            elif t.is_user_type():
                ptype = user_types_map[t]
            else:
                raise
            p = pytamer.tamer_parameter_new("p"+str(i), ptype)
            i += 1
            params.append(p)
        return pytamer.tamer_fluent_new(self.env, name, ttype, [], params)

    def _convert_action(self, action, fluents_map, user_types_map, instances_map):
        params = []
        params_map = {}
        for p in action.parameters():
            if p.type().is_bool_type():
                ptype = self.bool_type
            elif p.type().is_user_type():
                ptype = user_types_map[p.type()]
            else:
                raise
            new_p = pytamer.tamer_parameter_new(p.name(), ptype)
            params.append(new_p)
            params_map[p] = new_p
        expressions = []
        converter = Converter(self.env, fluents_map, instances_map, params_map)
        for c in action.preconditions():
            expr = pytamer.tamer_expr_make_temporal_expression(self.env, self.tamer_start,
                                                               converter.convert(c))
            expressions.append(expr)
        for f, v in action.effects():
            ass = pytamer.tamer_expr_make_assign(self.env, converter.convert(f), converter.convert(v))
            expr = pytamer.tamer_expr_make_temporal_expression(self.env, self.tamer_end, ass)
            expressions.append(expr)
        expr = pytamer.tamer_expr_make_assign(self.env, pytamer.tamer_expr_make_duration_anchor(self.env),
                                              pytamer.tamer_expr_make_integer_constant(self.env, 1))
        expressions.append(expr)
        return pytamer.tamer_action_new(self.env, action.name(), [], params, expressions)

    def _convert_problem(self, problem):
        user_types = []
        user_types_map = {}
        instances = []
        instances_map = {}
        for ut in problem.user_types().values():
            new_ut = pytamer.tamer_user_type_new(self.env, ut.name())
            user_types.append(new_ut)
            user_types_map[ut] = new_ut
            for obj in problem.objects(ut):
                new_obj = pytamer.tamer_instance_new(self.env, obj.name(), user_types_map[ut])
                instances.append(new_obj)
                instances_map[obj] = new_obj

        fluents = []
        fluents_map = {}
        for f in problem.fluents().values():
            new_f = self._convert_fluent(f, user_types_map)
            fluents.append(new_f)
            fluents_map[f] = new_f

        actions = []
        for a in problem.actions().values():
            new_a = self._convert_action(a, fluents_map, user_types_map, instances_map)
            actions.append(new_a)

        expressions = []
        converter = Converter(self.env, fluents_map, instances_map)
        for f, v in problem.initial_values().items():
            ass = pytamer.tamer_expr_make_assign(self.env, converter.convert(f), converter.convert(v))
            expr = pytamer.tamer_expr_make_temporal_expression(self.env, self.tamer_start, ass)
            expressions.append(expr)
        for g in problem.goals():
            expr = pytamer.tamer_expr_make_temporal_expression(self.env, self.tamer_end,
                                                               converter.convert(g))
            expressions.append(expr)

        return pytamer.tamer_problem_new(self.env, actions, fluents, [], instances, user_types, expressions)

    def _to_upf_plan(self, problem, ttplan):
        objects = {}
        for ut in problem.user_types().values():
            for obj in problem.objects(ut):
                objects[obj.name()] = obj
        actions = []
        for s in pytamer.tamer_ttplan_get_steps(ttplan):
            taction = pytamer.tamer_ttplan_step_get_action(s)
            name = pytamer.tamer_action_get_name(taction)
            action = problem.action(name)
            params = []
            for p in pytamer.tamer_ttplan_step_get_parameters(s):
                if pytamer.tamer_expr_is_boolean_constant(self.env, p) == 1:
                    new_p = upf.expression.Bool(pytamer.tamer_expr_get_boolean_constant(self.env, p) == 1)
                elif pytamer.tamer_expr_is_instance_reference(self.env, p) == 1:
                    i = pytamer.tamer_expr_get_instance(self.env, p)
                    new_p = objects[pytamer.tamer_instance_get_name(i)]
                else:
                    raise
                params.append(new_p)
            actions.append(upf.ActionInstance(action, tuple(params)))
        return upf.SequentialPlan(actions)

    def _solve(self, tproblem):
        potplan = pytamer.tamer_do_tsimple_planning(tproblem)
        ttplan = pytamer.tamer_ttplan_from_potplan(potplan)
        return ttplan

    def solve(self, problem):
        tproblem = self._convert_problem(problem)
        ttplan = self._solve(tproblem)
        return self._to_upf_plan(problem, ttplan)

    def destroy(self):
        pass