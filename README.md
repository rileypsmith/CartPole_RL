# CartPole_RL
A simple repository to implement reinforcement learning on the CartPole 
environment--just to practice RL and familiarize myself.

## DQN - My Implementation
In my implementation, I have used Deep Q-learning to solve the CartPole problem.

### The `Agent` class
I have chosen to setup a single class, which I call `Agent`. Within the `Agent`
class, both the Q-network and target-network are stored. The agent can be queried
at any time to provide a policy for a given state, and it contains built-in
functions for training (using SGD to update the weights of the Q-net) and
evaluation for convenience.

### The `ReplayBuffer` class
My replay buffer is a very lightweight class which essentially just uses the
agent to run episodes and populate a list until a certain list length is
reached. It has methods to sample that list randomly for training purposes and
to flush the buffer at the end of each epoch. 

### The `train` function
This is the main entrypoint for my implementation. It handles instantiation of
the agent and the replay buffer, and then runs a loop over many
epochs. In each one, it populates the replay buffer and trains the agent. It
also handles copying of the Q-network weights into the target network.