"""
Taken from Pytorch examples
"""

import argparse
import gym
import gym_tokens
import numpy as np
from itertools import count
import random

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Categorical

gamma = 1
seed = 5
lr= 0.5
render = False
log_interval = 1

env = gym.make('tokens-v0', gamma=0.75, seed=seed, terminal=15, fancy_discount=False)
env.seed(seed)
random.seed(seed)
torch.manual_seed(seed)

def _mapFromIndexToTrueActions(actions):
	if actions == 1:
		return -1 
	elif actions == 2:
		return 1
	else:
		return 0

in_dim = env.observation_space.shape[0]
out_dim = env.action_space.n
class Policy(nn.Module):
	def __init__(self):
		super(Policy, self).__init__()
		self.affine1 = nn.Linear(in_dim, 16)
		self.dropout = nn.Dropout(p=0.6)
		self.affine2 = nn.Linear(16, out_dim)

		self.saved_log_probs = []
		self.rewards = []

	def forward(self, x):
		x = self.affine1(x)
		x = self.dropout(x)
		x = F.relu(x)
		action_scores = self.affine2(x)
		return F.softmax(action_scores, dim=1)


policy = Policy()
# optimizer = optim.SGD(params=policy.parameters(), lr=lr)
# optimizer = optim.RMSprop(policy.parameters(), lr=lr)
optimizer = optim.Adam(policy.parameters(), lr=lr)
eps = np.finfo(np.float32).eps.item()


def select_action(state):
	state = torch.from_numpy(state).float().unsqueeze(0)
	probs = policy(state)
	m = Categorical(probs)
	action = m.sample()
	policy.saved_log_probs.append(m.log_prob(action))
	return action.item()


def finish_episode():
	R = 0
	policy_loss = []
	returns = []
	for r in policy.rewards[::-1]:
		R = r + gamma * R
		returns.insert(0, R)
	returns = torch.tensor(returns).float()
	returns = (returns - returns.mean()) / (returns.std() + eps)
	for log_prob, R in zip(policy.saved_log_probs, returns):
		policy_loss.append(-log_prob * R)
	optimizer.zero_grad()
	policy_loss = torch.cat(policy_loss).sum()
	policy_loss.backward()
	optimizer.step()
	del policy.rewards[:]
	del policy.saved_log_probs[:]


def _sign(num):
	'''
	This function determines the sign of the input value.
	: param num (int) : input
	: return num (int) : sign of input
	'''
	assert isinstance(num, np.int64)

	if num < 0:
		return -1

	elif num > 0:
		return 1

	else:
		return 0

returns = []
num_correct= 0
for i_episode in count(1):
	state, ts = env.reset()
	ep_reward = 0
	for t in range(1, 10000):  # Don't infinite loop while learning
	
		action = select_action(state)
		action = _mapFromIndexToTrueActions(action)

		#FIXME Actions are chosen even if they cause no effect on state.
		#their log prob is used to adjust the weight

		if ts == 15 and action == 0:
			action = random.choice([-1,1])

		state, reward, done, ts = env.step(action)

		if render:
			env.render()
		policy.rewards.append(reward)
		ep_reward += reward
		if done:
			returns.append(ep_reward)
			if (_sign(state[1]) == _sign(state[0])):
				num_correct += 1
			break

	finish_episode()
	if i_episode % log_interval == 0:
		print('Episode {}\tLast reward: {:.2f}\tAverage reward: {:.2f}\tAvg Correct: {:.2f}'.format(
				i_episode, ep_reward, np.mean(returns), num_correct/i_episode))