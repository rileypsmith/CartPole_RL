"""
Main Python script for implementing an agent trained on OpenAI's CartPole 
environment.
"""
import csv
import imageio
import random
import warnings

import gym
import numpy as np
from tqdm import tqdm
import tensorflow as tf
from tensorflow.keras import layers, Model, Sequential

warnings.simplefilter('ignore')

class Agent():
    """A class for containing q-net and t-net, plus all agent functions."""
    def __init__(self):
        # Setup networks
        self.q_net = self._build_net()
        self.t_net = self._build_net()
        self.update()

        self.epsilon = 1
        self.gamma = 0.9
    
    def _build_net(self):
        """Build the actual neural network component"""
        net = Sequential()
        net.add(layers.Dense(64, activation='relu',
                             kernel_initializer='he_uniform',
                             input_shape=(4,)))
        net.add(layers.Dense(64, activation='relu',
                             kernel_initializer='he_uniform'))
        net.add(layers.Dense(2, activation='linear',
                             kernel_initializer='he_uniform'))
        net.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
            loss=tf.keras.losses.MeanSquaredError()
        )
        return net
    
    def summary(self):
        self.q_net.summary()

    def policy(self, state, train=True):
        """
        Given a state, decide on a course of action.
        
        Parameters
        ----------
        state : ndarray
            Ndarray of shape (4,).
        """
        # Prepare for network
        net_input = tf.convert_to_tensor(state[np.newaxis,:])
        # Put it through the Q-Net
        q_est = self.q_net(net_input).numpy().ravel()
        # Choose optimal policy, or random policy according to epsilon
        if np.random.random() < self.epsilon and train:
            action = np.random.randint(0, 2)
        else:
            action = q_est.argmax()
        return action
    
    def train(self, batch):
        """
        Batch comes in as:

        state, action, reward, next state, done
        """
        # Setup network input
        states = tf.convert_to_tensor(np.stack([item[0] for item in batch], 
                                               axis=0))
        
        # Form 'truth' from next states and actual rewards
        next_states = tf.convert_to_tensor(np.stack([item[3] for item in batch], 
                                                    axis=0))
        truth = self.t_net(next_states).numpy()

        for i, (_, action, reward, _, done) in enumerate(batch):
            if done:
                truth[i, action] = reward
            else:
                truth[i, action] = reward + (self.gamma * truth[i, action])
        
        # Run SGD on the batch you just formed
        self.q_net.fit(states, truth, epochs=1)

    def run_episode(self, env, return_frames=False):
        # Start by resetting the environment
        state, _ = env.reset()
        done = False
        total_reward = 0
        frames = []
        while not done:
            action = self.policy(state, train=False)
            state, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            done = terminated or truncated
            if truncated:
                print('TRUNCATED')
            if return_frames:
                frames.append(env.render())
        if return_frames:
            return frames
        return total_reward

    def evaluate(self, env):
        """Run 100 episodes to see how long you can keep the pole up"""
        total_reward = 0
        for _ in range(100):
            total_reward += self.run_episode(env)
        return total_reward / 100
    
    def save_gif(self, env, episode):
        # Get frames
        frames = self.run_episode(env, return_frames=True)
        imageio.mimsave(f'episode{episode:03}.gif', frames)

    def update(self):
        """Copy the weights of the Q network over to the target network"""
        self.t_net.set_weights(self.q_net.get_weights())

    def update_epsilon(self):
        """Every episode, update epsilon"""
        if self.epsilon > 0.05:
            self.epsilon = np.max([self.epsilon * 0.9, 0.05])

class ReplayBuffer():
    """A class to handle all things related to the replay buffer"""
    def __init__(self, buffer_size=1280):

        self.buffer = []
        self.buffer_size = buffer_size

        self.end_factor = 0

    def store_experience(self, env, agent, state):
        # Implement agent's policy to get an action for this state
        action = agent.policy(state)
        # Get reward and next state from environment
        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        self.buffer.append((state, action, reward, next_state, done))
        return next_state, done

    def fill_buffer(self, env, agent):
        while len(self.buffer) < self.buffer_size:
            # Start by resetting environment
            state, _ = env.reset()
            done = False
            while not done:
                state, done = self.store_experience(env, agent, state)
                # If this episode is over or you hit random stopping point, reset
                # environment
                if done or np.random.random() < self.end_factor or len(self.buffer) >= self.buffer_size:
                    break

    def sample_buffer(self, batch_size=128):
        """Return a random sample from the buffer, without replacement"""
        for batch_num in range(0, self.buffer_size, batch_size):
            yield random.sample(self.buffer, batch_size)

    def update(self):
        self.replay_buffer = []
        self.end_factor *= 0.9

class CustomCSVWriter():
    """Super simple callback for writing to CSV file"""
    def __init__(self, csv_file):
        # Write headers to file
        self.csv_file = csv_file
        headers = ['Epoch', 'val_steps']
        with open(csv_file, 'w+', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
    def update(self, epoch, val_steps):
        with open(self.csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([epoch, val_steps])

def train(num_epochs=20):
    # Build an agent
    agent = Agent()
    # Setup replay buffer
    replay_buffer = ReplayBuffer()
    # Build environment
    env = gym.make('CartPole-v0', render_mode='rgb_array')
    log = CustomCSVWriter('test.csv')
    # Run a bunch of epochs of training
    for epoch in range(num_epochs):
        replay_buffer.fill_buffer(env, agent)
        for batch in replay_buffer.sample_buffer():
            agent.train(batch)
        # Run evaluation at the end of each epoch
        eval_result = agent.evaluate(env)
        log.update(epoch, eval_result)
        print(f'Epoch {epoch+1}/{num_epochs}: {eval_result}')

        # Update agent and buffer
        replay_buffer.update()
        agent.update_epsilon()
        agent.update()
        if (epoch + 1) % 2 == 0:
            agent.save_gif(env, epoch)
            # breakpoint()
        # env.render()
        


if __name__ == '__main__':
    train()

    


        