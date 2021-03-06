# -*- coding: utf-8 -*-
"""Copy of IITM_Assignment_2_Gridworld_Release.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/14zKzAfzuYR-xGpJPisEhEHpPjhn9pEgk

# What is the notebook about?

## Problem - Gridworld Environment Algorithms
This problem deals with a grid world and stochastic actions. The tasks you have to do are:
- Implement Policy Iteration
- Implement Value Iteration
- Implement TD lamdda
- Visualize the results
- Explain the results

## How to use this notebook? ๐

- This is a shared template and any edits you make here will not be saved.**You
should make a copy in your own drive**. Click the "File" menu (top-left), then "Save a Copy in Drive". You will be working in your copy however you like.

- **Update the config parameters**. You can define the common variables here

Variable | Description
--- | ---
`AICROWD_DATASET_PATH` | Path to the file containing test data. This should be an absolute path.
`AICROWD_RESULTS_DIR` | Path to write the output to.
`AICROWD_ASSETS_DIR` | In case your notebook needs additional files (like model weights, etc.,), you can add them to a directory and specify the path to the directory here (please specify relative path). The contents of this directory will be sent to AIcrowd for evaluation.
`AICROWD_API_KEY` | In order to submit your code to AIcrowd, you need to provide your account's API key. This key is available at https://www.aicrowd.com/participants/me

- **Installing packages**. Please use the [Install packages ๐](#install-packages-) section to install the packages

# Setup AIcrowd Utilities ๐ 

We use this to bundle the files for submission and create a submission on AIcrowd. Do not edit this block.
"""

!pip install aicrowd-cli > /dev/null

"""# AIcrowd Runtime Configuration ๐งท

Get login API key from https://www.aicrowd.com/participants/me
"""

import os

AICROWD_DATASET_PATH = os.getenv("DATASET_PATH", os.getcwd()+"/a5562c7d-55f0-4d06-841c-110655bb04ec_a2_gridworld_inputs.zip")
AICROWD_RESULTS_DIR = os.getenv("OUTPUTS_DIR", "results")
API_KEY = "a98ef81b017008edad014f38a0bb30ae" # Get your key from https://www.aicrowd.com/participants/me

!aicrowd login --api-key $API_KEY
!aicrowd dataset download -c iit-m-rl-assignment-2-gridworld

!unzip -q $AICROWD_DATASET_PATH

DATASET_DIR = 'inputs/'

"""# GridWorld Environment
Read the code for the environment thoroughly

Do not edit the code for the environment
"""

import numpy as np
from copy import deepcopy

class GridEnv_HW2:
    def __init__(self, 
                 goal_location, 
                 action_stochasticity,
                 non_terminal_reward,
                 terminal_reward,
                 grey_in,
                 brown_in,
                 grey_out,
                 brown_out
                ):

        # Do not edit this section 
        self.action_stochasticity = action_stochasticity
        self.non_terminal_reward = non_terminal_reward
        self.terminal_reward = terminal_reward
        self.grid_size = [10, 10]

        # Index of the actions 
        self.actions = {'N': (1, 0), 
                        'E': (0,1),
                        'S': (-1,0), 
                        'W': (0,-1)}
        
        self.perpendicular_order = ['N', 'E', 'S', 'W']
        
        l = ['normal' for _ in range(self.grid_size[0]) ]
        self.grid = np.array([l for _ in range(self.grid_size[1]) ], dtype=object)

        self.grid[goal_location[0], goal_location[1]] = 'goal'
        self.goal_location = goal_location

        for gi in grey_in:
            self.grid[gi[0],gi[1]] = 'grey_in'
        for bi in brown_in:    
            self.grid[bi[0], bi[1]] = 'brown_in'

        for go in grey_out:    
            self.grid[go[0], go[1]] = 'grey_out'
        for bo in brown_out:    
            self.grid[bo[0], bo[1]] = 'brown_out'

        self.grey_outs = grey_out
        self.brown_outs = brown_out

    def _out_of_grid(self, state):
        if state[0] < 0 or state[1] < 0:
            return True
        elif state[0] > self.grid_size[0] - 1:
            return True
        elif state[1] > self.grid_size[1] - 1:
            return True
        else:
            return False

    def _grid_state(self, state):
        return self.grid[state[0], state[1]]        
        
    def get_transition_probabilites_and_reward(self, state, action):
        """ 
        Returns the probabiltity of all possible transitions for the given action in the form:
        A list of tuples of (next_state, probability, reward)
        Note that based on number of state and action there can be many different next states
        Unless the state is All the probabilities of next states should add up to 1
        """

        grid_state = self._grid_state(state)
        
        if grid_state == 'goal':
            return [(self.goal_location, 1.0, 0.0)]
        elif grid_state == 'grey_in':
            npr = []
            for go in self.grey_outs:
                npr.append((go, 1/len(self.grey_outs), 
                            self.non_terminal_reward))
            return npr
        elif grid_state == 'brown_in':
            npr = []
            for bo in self.brown_outs:
                npr.append((bo, 1/len(self.brown_outs), 
                            self.non_terminal_reward))
            return npr
        
        direction = self.actions.get(action, None)
        if direction is None:
            raise ValueError("Invalid action %s , please select among" % action, list(self.actions.keys()))

        dir_index = self.perpendicular_order.index(action)
        wrap_acts = self.perpendicular_order[dir_index:] + self.perpendicular_order[:dir_index]
        next_state_probs = {}
        for prob, a in zip(self.action_stochasticity, wrap_acts):
            d = self.actions[a]
            next_state = (state[0] + d[0]), (state[1] + d[1])
            if self._out_of_grid(next_state):
                next_state = state
            next_state_probs.setdefault(next_state, 0.0)
            next_state_probs[next_state] += prob

        npr = []
        for ns, prob in next_state_probs.items():
            next_grid_state = self._grid_state(ns)
            reward = self.terminal_reward if next_grid_state == 'goal' else self.non_terminal_reward
            npr.append((ns, prob, reward))

        return npr

    def step(self, state, action):
        npr = self.get_transition_probabilites_and_reward(state, action)
        probs = [t[1] for t in npr]
        sampled_idx = np.random.choice(range(len(npr)), p=probs)
        sampled_npr = npr[sampled_idx]
        next_state = sampled_npr[0]
        reward = sampled_npr[2]
        is_terminal = next_state == tuple(self.goal_location)
        return next_state, reward, is_terminal

"""## Example environment

This has the same setup as the pdf, do not edit the settings
"""

def get_base_kwargs():
    goal_location = (9,9)
    action_stochasticity = [0.8, 0.2/3, 0.2/3, 0.2/3]
    grey_out = [(3,2), (4,2), (5,2), (6,2)]
    brown_in = [(9,7)]
    grey_in = [(0,0)]
    brown_out = [(1,7)]
    non_terminal_reward = 0
    terminal_reward = 10

    base_kwargs =  {"goal_location": goal_location, 
            "action_stochasticity": action_stochasticity,
            "brown_in": brown_in, 
            "grey_in": grey_in, 
            "brown_out": brown_out,
            "non_terminal_reward": non_terminal_reward,
            "terminal_reward": terminal_reward,
            "grey_out": grey_out,}
    
    return base_kwargs

base_kwargs = get_base_kwargs()

"""## Task 2.1 - Value Iteration
Run value iteration on the environment and generate the policy and expected reward
"""

def value_iteration(env, gamma):
    # Initial Values
    values = np.zeros((10, 10))

    # Initial policy
    policy = np.empty((10, 10), object)
    policy[:] = 'N' # Make all the policy values as 'N'

    # Begin code here
    value_grids = [] # Store all the J(s) grids at every iteration in this list
    policies = []  # Store all the pi(s) grids at every iteration in this list

    val = np.zeros((10,10))
    pol = np.empty((10, 10), object)
    pol[:] = 'N'

  
    l = -1
    value_grid1 = np.zeros((10,10))
    policy_grid1 = np.zeros((10, 10), np.int32)
    while(True):
      l = l+1
      for i in range(10):
        for j in range(10):
              value = np.NINF
              policy1 = ''
              for actions in env.perpendicular_order :
                  nspr = env.get_transition_probabilites_and_reward((i,j), actions)
                  prob = deepcopy([ nspr[k][1] for k in range(len(nspr))])
                  ns = deepcopy([(nspr[k][0][0],nspr[k][0][1]) for k in range(len(nspr))])
                  rew = deepcopy([nspr[k][2] for k in range(len(nspr))])
                  value_grid1[i][j] =  sum( [ prob[k]*(rew[k] + gamma*values[ns[k][0]][ns[k][1]]) for k in range(len(nspr))])

                  if value != value_grid1[i][j]:
                    value = deepcopy(max(value_grid1[i][j], value))
                    if value == value_grid1[i][j]:
                      policy1 = deepcopy(actions)

              values[i][j] = deepcopy(value)
              policy[i][j] = deepcopy(policy1)

      value_grids.append(deepcopy(values))
      policies.append(deepcopy(policy))

      if l>=1:
        converge = deepcopy(np.amax(np.absolute(value_grids[l]-value_grids[l-1])))
        if converge < 1e-8:
            #print(l)
            #print(value_grids[l])           #Uncomment these lines to print the output
            #print(policies[l])
            break

    """for i in range(10):
      for j in range(10):
        values[i][j] = val[9-i][j]
        policy[i][j] = pol[9-i][j] """




        


    # Put your extra information needed for plots etc in this dictionary
    extra_info = {}

    # End code

    # Do not change the number of output values
    return {"Values": values, "Policy": policy}, extra_info

env = GridEnv_HW2(**base_kwargs)
res, extra_info = value_iteration(env, 0.7)

 # The rounding off is just for making print statement cleaner
print(np.flipud(np.round(res['Values'], decimals=2)))
print(np.flipud(res['Policy']))

"""## Task 2.2 - Policy Iteration
Run policy iteration on the environment and generate the policy and expected reward
"""

def policy_iteration(env, gamma):
    # Initial Values
    values = np.zeros((10, 10))

    # Initial policy
    policy = np.empty((10, 10), object)
    policy[:] = 'N' # Make all the policy values as 'N'

    # Begin code here  

    value_grids = [] # Store all the J(s) grids at every iteration in this list
    policies = []  # Store all the pi(s) grids at every iteration in this list


    done = 0

    while done == 0:  
      done = 1
      l = -1

      while True:
        delta = np.NINF
        l = l+1
        value_grid1 = np.zeros((10,10))
        policy_grid1 = np.zeros((10, 10), np.int32)
        J = 0
        for i in range(10):
          for j in range(10):
                value = deepcopy(np.NINF)
                nspr = deepcopy( env.get_transition_probabilites_and_reward((i,j), policy[i][j]) )
                prob = deepcopy([ nspr[k][1] for k in range(len(nspr))])
                ns = deepcopy([(nspr[k][0][0],nspr[k][0][1]) for k in range(len(nspr))])
                rew = deepcopy([nspr[k][2] for k in range(len(nspr))])
                J = values[i][j]
                value_grid1[i][j] =  deepcopy( sum( [ prob[k]*(rew[k] + gamma*values[ns[k][0]][ns[k][1]]) for k in range(len(nspr))]) )
                delta = deepcopy( max(delta, np.abs(J - value_grid1[i][j])) )
        for i in range(10):
          for j in range(10):
                values[i][j] = deepcopy(value_grid1[i][j])
        if delta < 1e-8:
          break

      b = np.empty((10, 10), object)
      for i in range(10):
        for j in range(10):
              value = deepcopy(np.NINF)
              policy1 = ''
              b[i][j] = deepcopy(policy[i][j])
              for actions in env.perpendicular_order :
                  nspr = env.get_transition_probabilites_and_reward((i,j), actions)
                  prob = deepcopy([ nspr[k][1] for k in range(len(nspr))])
                  ns = deepcopy([(nspr[k][0][0],nspr[k][0][1]) for k in range(len(nspr))])
                  rew = deepcopy([nspr[k][2] for k in range(len(nspr))])
                  value_grid1[i][j] =  deepcopy( sum( [ prob[k]*(rew[k] + gamma*values[ns[k][0]][ns[k][1]]) for k in range(len(nspr))]) )

                  if value != value_grid1[i][j]:
                    value = deepcopy(max(value_grid1[i][j], value))
                    if value == value_grid1[i][j]:
                      policy1 = deepcopy(actions)
              value_grid1[i][j] = deepcopy(value)
              policy[i][j] = deepcopy(policy1)
      
      for i in range(10):
        for j in range(10):
              values[i][j] = deepcopy(value_grid1[i][j])
      for i in range(10):
        for j in range(10):
              if b[i][j] != policy[i][j]:
                done = 0
      value_grids.append(deepcopy(values))
      policies.append(deepcopy(policy))

      """  if l>=1:
          converge = deepcopy(np.amax(np.absolute(value_grids[l]-value_grids[l-1])))
          if converge < 1e-8:
              #print(l)
              #print(value_grids[l])           #Uncomment these lines to print the output
              #print(policies[l])
              break"""


    # Put your extra information needed for plots etc in this dictionary
    extra_info = {}
    extra_info["Values"] = value_grids
    extra_info["Policy"] = policies

    # End code

    # Do not change the number of output values
    return {"Values": values, "Policy": policy}, extra_info

env = GridEnv_HW2(**base_kwargs)
res, extra_info = policy_iteration(env, 0.7)

 # The rounding off is just for making print statement cleaner
print(np.flipud(np.round(res['Values'], decimals=2)))
print(np.flipud(res['Policy']))

"""# Task 2.3 - TD Lambda

Use the heuristic policy and implement TD lambda to find values on the gridworld
"""

# The policy mentioned in the pdf to be used for TD lambda, do not modify this
def heuristic_policy(env, state):
    goal = env.goal_location
    dx = goal[0] - state[0]
    dy = goal[1] - state[1]
    target_action = 'N'
    if abs(dx) >= abs(dy):
        direction = (np.sign(dx), 0)
    else:
        direction = (0, np.sign(dy))
    for action, dir_val in env.actions.items():
        if dir_val == direction:
            target_action = action
            break
    return target_action

def td_lambda(env, lamda, seeds):
    alpha = 0.5
    gamma = 0.7
    N = len(seeds)
    # Usage of input_policy
    # heuristic_policy(env, state) -> action
    example_action = heuristic_policy(env, (1,2)) # Returns 'N' if goal is (9,9)
    value_grid = [] # Store all the J(s) grids at every iteration in this list

    # Example of env.step
    # env.step(state, action) -> Returns next_state, reward, is_terminal

    # Initial values
    values = np.zeros((10, 10))
    es = np.zeros((10,10))

    for episode_idx in range(N):
         # Do not change this else the results will not match due to environment stochas
        np.random.seed(seeds[episode_idx])
        grey_in_loc = np.where(env.grid == 'grey_in')
        state = grey_in_loc[0][0], grey_in_loc[1][0]
        done = False
        while not done:
            action = heuristic_policy(env, state)
            ns, rew, is_terminal = env.step(state, action) 
            # env.step is already taken inside the loop for you, 
            # Don't use env.step anywhere else in your code

            # Begin code here
            delta = rew - values[state[0]][state[1]] + gamma*values[ns[0]][ns[1]]
            es[state[0]][state[1]] = es[state[0]][state[1]] + 1
            for i in range(10):
              for j in range(10):
                values[i][j] = values[i][j] + alpha*delta*es[i][j]
                es[i][j] = gamma*lamda*es[i][j]
            a, b = ns
            state = (a,b)
            value_grid.append(values)
            if is_terminal:
              break


    # Put your extra information needed for plots etc in this dictionary
    extra_info = {}
    extra_info["Values"] = value_grid

    # End code

    # Do not change the number of output values
    return {"Values": values}, extra_info

env = GridEnv_HW2(**base_kwargs)
res, extra_info = td_lambda(env, lamda=0.5, seeds=np.arange(1000))

 # The rounding off is just for making print statement cleaner
print(np.flipud(np.round(res['Values'], decimals=2)))

"""# Task 2.4 - TD Lamdba for multiple values of $\lambda$

Ideally this code should run as is
"""

# This cell is only for your subjective evaluation results, display the results as asked in the pdf
# You can change it as you require, this code should run TD lamdba by default for different values of lambda

lamda_values = np.arange(0, 100+5, 5)/100
td_lamda_results = {}
extra_info = {}
for lamda in lamda_values:
    env = GridEnv_HW2(**base_kwargs)
    td_lamda_results[lamda], extra_info[lamda] = td_lambda(env, lamda,
                                                           seeds=np.arange(1000))

"""# Generate Results โ"""

def get_results(kwargs):

    gridenv = GridEnv_HW2(**kwargs)

    policy_iteration_results = policy_iteration(gridenv, 0.7)[0]
    value_iteration_results = value_iteration(gridenv, 0.7)[0]
    td_lambda_results = td_lambda(env, 0.5, np.arange(1000))[0]

    final_results = {}
    final_results["policy_iteration"] = policy_iteration_results
    final_results["value_iteration"] = value_iteration_results
    final_results["td_lambda"] = td_lambda_results

    return final_results

# Do not edit this cell, generate results with it as is
if not os.path.exists(AICROWD_RESULTS_DIR):
    os.mkdir(AICROWD_RESULTS_DIR)

for params_file in os.listdir(DATASET_DIR):
  kwargs = np.load(os.path.join(DATASET_DIR, params_file), allow_pickle=True).item()
  results = get_results(kwargs)
  idx = params_file.split('_')[-1][:-4]
  np.save(os.path.join(AICROWD_RESULTS_DIR, 'results_' + idx), results)

"""# Check your score on the public data

This scores is not your final score, and it doesn't use the marks weightages. This is only for your reference of how arrays are matched and with what tolerance.
"""

# Check your score on the given test cases (There are more private test cases not provided)
target_folder = 'targets'
result_folder = AICROWD_RESULTS_DIR

def check_algo_match(results, targets):
    if 'Policy' in results:
        policy_match = results['Policy'] == targets['Policy']
    else:
        policy_match = True
    # Reference https://numpy.org/doc/stable/reference/generated/numpy.allclose.html
    rewards_match = np.allclose(results['Values'], targets['Values'], rtol=3)
    equal = rewards_match and policy_match
    return equal

def check_score(target_folder, result_folder):
    match = []
    for out_file in os.listdir(result_folder):
        res_file = os.path.join(result_folder, out_file)
        results = np.load(res_file, allow_pickle=True).item()
        idx = out_file.split('_')[-1][:-4]  # Extract the file number
        target_file = os.path.join(target_folder, f"targets_{idx}.npy")
        targets = np.load(target_file, allow_pickle=True).item()
        algo_match = []
        for k in targets:
            algo_results = results[k]
            algo_targets = targets[k]
            algo_match.append(check_algo_match(algo_results, algo_targets))
        match.append(np.mean(algo_match))
    return np.mean(match)

if os.path.exists(target_folder):
    print("Shared data Score (normalized to 1):", check_score(target_folder, result_folder))

"""## Display Results of TD lambda 
Display Results of TD lambda with lambda values from 0 to 1 with steps of 0.05

Add code/text as required

"""

lamda_values = np.arange(0, 100+5, 5)/100
td_lamda_results = {}
extra_info = {}
for lamda in lamda_values:
    env = GridEnv_HW2(**base_kwargs)
    td_lamda_results[lamda], extra_info[lamda] = td_lambda(env, lamda,
                                                           seeds=np.arange(1000))
    print("lamda :", lamda)
    print(np.round(td_lamda_results[lamda]['Values'], decimals=2), "\n")

"""# Subjective questions

## 2.a Value Iteration vs Policy Iteration


1.   Compare value iteration and policy iteration for states Brown in, Brown Out, Grey out and Grey In 
2.   Which one converges faster and why

## 2.b How changing $\lambda$ affecting TD Lambda

## 2.c Policy iteration error curve
Plot error curve of $J_i$ vs iteration $i$ for policy iteration
"""

env = GridEnv_HW2(**base_kwargs)
res, extra_info = policy_iteration(env, 0.7)

value_grid = extra_info["Values"]

import matplotlib.pyplot as plt
diffs = []
for ii in range(len(value_grid)-1):
    diff = np.linalg.norm(value_grid[ii+1]-value_grid[ii]) 
    diffs.append(diff)
plt.plot(diffs)

"""## 2.d TD Lamdba error curve
Plot error curve of $J_i$ vs iteration $i$ for TD Lambda for $\lambda = [0, 0.25, 0.5, 0.75, 1]$
"""

env = GridEnv_HW2(**base_kwargs)
res, extra_info = td_lambda(env, lamda=0.5, seeds=np.arange(1000))

import matplotlib.pyplot as plt

for lamda in [0,0.25,0.5,0.75,1]:
  diffs = []
  res, extra_info = td_lambda(env, lamda, seeds=np.arange(1000))
  value_grid = extra_info["Values"]
  for ii in range(len(value_grid)-1):
      diff = np.sqrt((value_grid[ii+1] - value_grid[ii])/100) 
      diffs.append(diff)
  plt.plot(diffs)
  plt.show()

"""# Submit to AIcrowd ๐"""

!DATASET_PATH=$AICROWD_DATASET_PATH aicrowd notebook submit --no-verify -c iit-m-rl-assignment-2-gridworld -a assets

