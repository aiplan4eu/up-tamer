# Tamer integration for unified-planning
[Tamer](https://tamer.fbk.eu/) is an application-oriented planner for the ANML planning specification language.
The objective of Tamer is to provide functionalities to model, solve and analyze planning problems in practice, with advanced temporal features.


## Tamer engine

The Tamer engine supports **action-based planning**, with the following features:

 - **classical**: basic action models with symbolic state variables
 - **numeric**: support numeric planning over *integer* and *real* state variables.
 - **temporal**: durative actions, intermediate conditions and effects, timed initial literals, timed goals. Support continuous time semantics.


Provided engines:

 - **tamer**:
   - **oneshot planning**: Will return the first plan found, regardless of its quality.
   - **plan validation**: Will analyze a plan and return if the plan is valid or not.


## Default configuration
The Tamer integration for unified-planning uses an heuristic search algorithm to solve the planning problem.
More specifically, the default search is a Weighted A* Search, with **weight** equals to **0.8** and **hadd** as **heuristic**.

The custom parameters are:
- **weight**: a float between **0.0** and **1.0**,
- **heuristic**: a string between **hadd**, **hlandmarks**, **hmax**, **hff** and **blind**.

## Installation

To automatically get a version that works with your version of the unified planning framework, you can list it as a solver in the pip installation of ```unified_planning```:

```
pip install unified-planning[tamer]
```

If you need several solvers, you can list them all within the brackets.

You can also install the Tamer integration separately (in case the current version of unified_planning does not include Tamer or you want to add it later to your unified planning installation). With

```
pip install up-tamer
```

you get the latest version. If you need an older version, you can install it with:

```
pip install up-tamer==<version number>
```

If you need the latest pre-release version, you can install it with:

```
pip install --pre up-tamer
```
or if you already have a version installed:
```
pip install --pre --upgrade up-tamer
```

## References
- [Alessandro Valentini, Andrea Micheli and Alessandro Cimatti. *Temporal Planning with Intermediate Conditions and Effects*. In AAAI 2020.](https://ojs.aaai.org//index.php/AAAI/article/view/6553)

## Acknowledgments
<img src="https://www.aiplan4eu-project.eu/wp-content/uploads/2021/07/euflag.png" width="60" height="40">

This library is being developed for the AIPlan4EU H2020 project (https://aiplan4eu-project.eu) that is funded by the European Commission under grant agreement number 101016442.
