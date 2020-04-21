import numpy as np

class Weight:
	def __init__(self, dimension, converge_val, height, shape): 
		self.w = np.zeros(dimension)
		self.converge_val = converge_val
		self.height = height
		self.shape = shape

	def get_qVal(self, state_action_rep):
		return np.dot(self.w, state_action_rep)

	def update_weight(self, learning_rate, td_error):
		temp = self.w.copy()
		self.w += learning_rate * td_error

		if self._hasConverged(temp, self.w):
			return True
		else:
			return False

	def _hasConverged(self, q_mat1, q_mat2):
		diff = np.linalg.norm(q_mat1 - q_mat2)

		if abs(diff) < self.converge_val:
			return True

		else: 
			return False

	def get_error(self, state, action, next_state, next_action , reward, gamma, is_done, model2 = None):
		state_action_rep = self._one_hot(state, action, self.shape)
		current_qVal = self.get_qVal(state_action_rep)

		if is_done:
			next_qVal = 0
		else:
			next_state_action_rep = self._one_hot(next_state,next_action, self.shape)
			next_qVal = self.get_qVal(next_state_action_rep)

		return (reward + (gamma*next_qVal) - current_qVal)*state_action_rep

	def save_w(self, file, timestep):
		np.save(file+'/w_'+str(timestep), self.w)

	def _one_hot(self, state, action, shape):
		Nt, ht, height, A = shape
		one = np.eye(Nt)[self._augState(state[0],height)]
		two = np.eye(ht)[self._augState(state[1],height)]
		three = np.eye(height)[state[2]]
		four = np.eye(A)[self._mapFromTrueActionsToIndex(action)]
		return np.hstack((one,two,three,four))

	def _augState(self, stateVal, height):
		"""
		Eg. Augment state value so that [-15,15] goes to [0,30] 
		"""
		return stateVal + height

	def _mapFromTrueActionsToIndex(self, actions):
		if actions == -1:
			return 1 
		elif actions == 1:
			return 2
		else:
			return 0 
