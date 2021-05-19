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
    def solve(self, problem):
        env = pytamer.tamer_env_new()

        fluents = []
        fluents_map = {}
        bool_type = pytamer.tamer_boolean_type(env)
        for f in problem.fluents().values():
            name = f.name()
            typename = f.type()
            if typename.is_bool_type():
                ttype = bool_type
            else:
                raise
            params = []
            i = 0
            for t in f.signature():
                if t.is_bool_type():
                    ptype = bool_type
                else:
                    raise
                p = pytamer.tamer_parameter_new("p"+str(i), ptype)
                i += 1
                params.append(p)
            new_f = pytamer.tamer_fluent_new(env, name, ttype, [], 0, params, len(params))
            fluents.append(new_f)
            fluents_map[f] = new_f

        actions = []
        for a in problem.actions().values():
            params = []
            params_map = {}
            for p in a.parameters():
                if p.type().is_bool_type():
                    ptype = bool_type
                else:
                    raise
                new_p = pytamer.tamer_parameter_new(p.name(), ptype)
                params.append(new_p)
                params_map[p] = new_p
            expressions = []
            converter = Converter(env, fluents_map, params_map)
            for c in a.preconditions():
                i = pytamer.tamer_expr_make_point_interval(env, pytamer.tamer_expr_make_start_anchor(env))
                expr = pytamer.tamer_expr_make_temporal_expression(env, i, converter.convert(c))
                expressions.append(expr)
            for f, v in a.effects():
                i = pytamer.tamer_expr_make_point_interval(env, pytamer.tamer_expr_make_start_anchor(env))
                ass = pytamer.tamer_expr_make_assign(env, converter.convert(f), converter.convert(v))
                expr = pytamer.tamer_expr_make_temporal_expression(env, i, ass)
                expressions.append(expr)
            expr = pytamer.tamer_expr_make_assign(env, pytamer.tamer_expr_make_duration_anchor(env),
                                                  pytamer.tamer_expr_make_integer_constant(env, 1))
            expressions.append(expr)
            new_a = pytamer.tamer_action_new(env, a.name(), [], 0, params, len(params),
                                             expressions, len(expressions))
            actions.append(new_a)

        converter = Converter(env, fluents_map)
        expressions = []
        for f, v in problem.initial_values().items():
            i = pytamer.tamer_expr_make_point_interval(env, pytamer.tamer_expr_make_start_anchor(env))
            ass = pytamer.tamer_expr_make_assign(env, converter.convert(f), converter.convert(v))
            expr = pytamer.tamer_expr_make_temporal_expression(env, i, ass)
            expressions.append(expr)
        for g in problem.goals():
            i = pytamer.tamer_expr_make_point_interval(env, pytamer.tamer_expr_make_end_anchor(env))
            expr = pytamer.tamer_expr_make_temporal_expression(env, i, converter.convert(g))
            expressions.append(expr)

        tproblem = pytamer.tamer_problem_new(env, actions, len(actions), fluents, len(fluents),
                                             [], 0, [], 0, [], 0, expressions, len(expressions))

        potplan = pytamer.tamer_do_tsimple_planning(tproblem)
        ttplan = pytamer.tamer_ttplan_from_potplan(potplan)

        actions = []
        for s in pytamer.tamer_ttplan_get_steps(ttplan):
            taction = pytamer.tamer_ttplan_step_get_action(s)
            n = pytamer.tamer_ttplan_step_get_num_parameters(s)
            params = []
            for i in range(n):
                p = pytamer.tamer_ttplan_step_get_parameter(s, i)
                if pytamer.tamer_expr_is_boolean_constant(env, p) == 1:
                    new_p = upf.expression.Bool(pytamer.tamer_expr_get_boolean_constant(env, p) == 1)
                else:
                    raise
                params.append(new_p)

            action = problem.action(pytamer.tamer_action_get_name(taction))
            actions.append(upf.ActionInstance(action, tuple(params)))

        return upf.SequentialPlan(actions)

    def destroy(self):
        pass
