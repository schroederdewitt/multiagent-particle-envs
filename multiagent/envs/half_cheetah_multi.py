import numpy as np
import gym
from multiagent.environment import MultiAgentEnv
from multiagent.envs import obsk

# using code from https://github.com/ikostrikov/pytorch-ddpg-naf
class NormalizedActions(gym.ActionWrapper):

    def _action(self, action):
        action = (action + 1) / 2  # [-1, 1] => [0, 1]
        action *= (self.action_space.high - self.action_space.low)
        action += self.action_space.low
        return action

    def action(self, action_):
        return self._action(action_)

    def _reverse_action(self, action):
        action -= self.action_space.low
        action /= (self.action_space.high - self.action_space.low)
        action = action * 2 - 1
        return action

class MultiAgentHalfCheetah(MultiAgentEnv):

    def __init__(self, arglist):
        super().__init__()

        self.agent_conf = getattr(arglist, "agent_conf", "3x3")

        self.agent_partitions, self.mujoco_edges  = obsk.get_parts_and_edges("half_cheetah",
                                                                             self.agent_conf)

        self.n_agents = len(self.agent_partitions)
        self.n_actions = max([len(l) for l in self.agent_partitions])

        self.agent_obsk = getattr(arglist,
                                  "agent_obsk",
                                  None)
        # if None, fully observable else k>=0 implies observe nearest k agents or joints
        self.agent_obsk_agents = getattr(arglist,
                                         "agent_obsk_agents",
                                         False)
        # observe full k nearest agents (True) or just single joints (False)

        if self.agent_obsk is not None:
            self.k_dicts = [obsk.get_joints_at_kdist(agent_id,
                                                    self.agent_partitions,
                                                    self.mujoco_edges,
                                                    k=self.agent_obsk,
                                                    kagents=False,) for agent_id in range(self.n_agents)]

        # load scenario from script
        self.episode_limit = self.args.episode_limit

        self.env_version = getattr(arglist, "env_version", 2)
        if self.env_version == 2:
            self.wrapped_env = NormalizedActions(gym.make('HalfCheetah-v2'))
        else:
            assert False,  "not implemented!"
            self.wrapped_env = NormalizedActions(gym.make('HalfCheetah-v3'))
        self.timelimit_env = self.wrapped_env.env
        self.timelimit_env._max_episode_steps = self.episode_limit
        self.env = self.timelimit_env.env
        self.timelimit_env.reset()
        self.obs_size = self.get_obs_size()
        pass

    def step(self, action_n):

        flat_actions = np.concatenate([action_n[i] for i in range(action_n.shape[0])])
        obs_n, reward_n, done_n, info_n = self.wrapped_env.step(flat_actions)
        self.steps += 1

        info = {}
        info.update(info_n)

        # NOTE: Gym wraps the InvertedPendulum and HalfCheetah envs by default with TimeLimit env wrappers,
        # which means env._max_episode_steps=1000. The env will terminate at the 1000th timestep by default.
        # Here, the next state will always be masked out
        # terminated = done_n
        # if self.steps >= self.episode_limit and not done_n:
        #     # Terminate if episode_limit is reached
        #     terminated = True
        #     info["episode_limit"] = getattr(self, "truncate_episodes", True)  # by default True
        # else:
        #     info["episode_limit"] = False

        if done_n:
            if self.steps < self.episode_limit:
                info["episode_limit"] = False   # the next state will be masked out
            else:
                info["episode_limit"] = True    # the next state will not be masked out

        return obs_n, reward_n, done_n, info

    def reset(self):
        self.steps = 0
        self.timelimit_env.reset()
        return self._get_obs_all()

    def _get_info(self, agent):
        pass

    def _get_obs_all(self):
        """ Returns all agent observations in a list """
        obs_n = []
        for a in range(self.n_agents):
            obs_n.append(self.get_obs_agent(a))
        return obs_n

    def _get_obs(self, agent_id):
        if self.agent_obsk is None:
            return self.env._get_obs()
        else:
            return obsk.build_obs(self.k_dicts[agent_id],
                                  self.env.sim.data.qpos,
                                  self.env.sim.data.qvel,
                                  vec_len=self.obs_size)

    def _get_done(self, agent):
        pass

    def _get_reward(self, agent):
        pass

    def _set_action(self, action, agent, action_space, time=None):
        pass

    def _reset_render(self):
        pass

    def render(self, mode='human'):
        pass

    def _make_receptor_locations(self, agent):
        pass
