# fast_gym environments

## fastlib.py

Wrapper of OpenFast .dll into python

## fast_gym_base.py

Wrapper of fastlib.py whith Gym API. It serves as base class for next environments.


## fast_gym_n.py

Each n env, inherits from FastGymBase, and extends it with:

- New action and observation space:         super().set_spaces(low_action, high_action, low_obs, high_obs)
- map_inputs
- map_outputs
- Reward