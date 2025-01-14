import numpy as np
from scipy.special import softmax
import torch
import torch.nn as nn

class Policy:
	"""
	Abstract class that converts Q-values to actions
	"""

	def __call__(self, scores):
		raise NotImplementedError

class GreedyPolicy(Policy):
	"""
	Select actions that maximizes the Q-values
	"""

	def __call__(self, scores):
		assert isinstance(scores, np.ndarray)
		if np.all(scores == scores[0]):
			return np.random.choice(len(scores))
		else:
			return np.argmax(scores, axis=0)

class EpsilonGreedyPolicy(Policy):
	"""
	Select random actions with prob <= epsilon, else select greedy actions
	"""

	def __init__(self, epsilon=0.01, default_policy=GreedyPolicy()):
		self.epsilon = epsilon
		self.default_policy = default_policy

	def __call__(self, scores):
		assert isinstance(scores, np.ndarray)

		num_actions = len(scores)
		eps_mask = np.random.random(size=1) < self.epsilon
		actions = self.default_policy(scores)
		rand_actions = np.random.choice(num_actions, size=sum(eps_mask))
		
		if eps_mask:

			return rand_actions, None

		else:
			return actions, None


class EpsilonGreedyBiasedPolicy(Policy):
	"""
	Select random actions with prob <= epsilon, else select greedy actions
	"""

	def __init__(self, epsilon=0.01, default_policy=GreedyPolicy()):
		self.epsilon = epsilon
		self.default_policy = default_policy

	def __call__(self, scores):
		assert isinstance(scores, np.ndarray)
		num_actions = len(scores)
		eps_mask = np.random.random(size=1) < self.epsilon
		actions = self.default_policy(scores)

		prob_wait_action = 1/3 + self.epsilon
		prob_left_right_action = 1/3-(self.epsilon/2)
		rand_actions = np.random.choice(num_actions, size=sum(eps_mask), p=[prob_wait_action, prob_left_right_action, prob_left_right_action])

		if eps_mask:
			return rand_actions, None

		else:
			return actions, None

class EpsilonGreedyGamePolicy(Policy):
	"""
	Select random actions with prob <= epsilon, else select greedy actions
	"""

	def __init__(self, epsilon=0.01, default_policy=GreedyPolicy()):
		self.epsilon = epsilon
		self.default_policy = default_policy

	def __call__(self, scores):
		assert isinstance(scores, np.ndarray)
		num_actions = len(scores)
		eps_mask = np.random.random(size=1) < self.epsilon
		actions = self.default_policy(scores)

		prob_left_right_action = (1-self.epsilon)/2
		rand_actions = np.random.choice(num_actions, size=sum(eps_mask), p=[self.epsilon, prob_left_right_action, prob_left_right_action])

		if eps_mask:
			return rand_actions, None

		else:
			return actions, None

class EpsilonGreedyGameDecisionPolicy(Policy):
	"""
	Select random actions with prob <= epsilon, else select greedy actions.
	If game has reach final step and the chosen action is wait, chose left or right uniform randomly.

	"""

	def __init__(self, epsilon=0.01, default_policy=GreedyPolicy()):
		self.epsilon = epsilon
		self.default_policy = default_policy

	def __call__(self, scores):
		assert isinstance(scores, np.ndarray)
		num_actions = len(scores)
		eps_mask = np.random.random(size=1) < self.epsilon
		actions = self.default_policy(scores)

		prob_left_right_action = (1-self.epsilon)/2
		rand_actions = np.random.choice(num_actions, size=sum(eps_mask), p=[self.epsilon, prob_left_right_action, prob_left_right_action])


		if eps_mask:
			return rand_actions, None

		else:
			return actions, None

class SoftmaxPolicy(Policy):
	"""
	Choose actions according to their softmax probabilty
	"""

	def __init__(self, temperature = 1):
		self.temperature: float = temperature

	def __call__(self, scores):
		assert isinstance(scores, np.ndarray)
		num_actions = len(scores)
		probs = softmax(scores/self.temperature)
		action = np.random.choice(num_actions, p = probs)
		return action, probs

class EpsilonSoftPolicy(Policy):
	"""
	Choose actions according to their softmax probabilty
	"""

	def __init__(self, epsilon = 0.01):
		self.epsilon = epsilon

	def __call__(self, scores):
		assert isinstance(scores, np.ndarray)
		num_actions = len(scores)
		probs = [self.epsilon/float(num_actions)]*num_actions
		probs[np.argmax(scores)] += 1 - self.epsilon
		action = np.random.choice(num_actions, p = probs)
		return action, probs


class EpsilonTracker():

	def __init__(self, eps_start, eps_final, num_frames, policy):
		self.eps_start = eps_start
		self.eps_final = eps_final
		self.num_frames = num_frames
		self.policy = policy

	def set_eps(self, frame):
		eps = self.eps_start - frame/float(self.num_frames)
		self.policy.epsilon =  max(eps, self.eps_final)


class TemperatureTracker():

	def __init__(self, tmp_start, tmp_final, num_frames, policy):
		self.tmp_start = tmp_start
		self.tmp_final = tmp_final
		self.num_frames = num_frames
		self.policy = policy

	def set_tmp(self, frame):
		tmp = self.tmp_start - frame/float(self.num_frames)
		self.policy.temperature =  max(tmp, self.tmp_final)


class PolicyNetwork(nn.Module):
  def __init__(self, in_dim, h_dim, out_dim):
    super(PolicyNetwork, self).__init__()
    self.linear_1 = nn.Linear(in_dim, h_dim, bias=True)
    self.relu_1 = nn.ReLU()
    self.linear_2 = nn.Linear(h_dim, out_dim, bias=True)
    self.softmax = nn.Softmax(dim=1)

  def forward(self, input):
    o_1 = self.linear_1(input)
    o_2 = self.relu_1(o_1)
    o_3 = self.linear_2(o_2)
    o_4 = self.softmax(o_3)
    return o_4