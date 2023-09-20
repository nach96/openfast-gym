import numpy as np
import gym
from gym import spaces
from fastlib import FastLib as fl
import os
import sys
import ctypes.util

input_file_name = "G:\\Mi unidad\\0_TFM\\Concurso CEA\\Berchmark_CIC2023_CategoriaMaster\\FAST_1\\IEA-15-240-RWT-Monopile.fst"
library_rel_path = "..\\dependencies\\openfastlib.dll"
class FastGymBase(fl,gym.Env):
    def __init__(self, inputFileName=input_file_name, libraryPath=library_rel_path, max_time=40, Tem_ini=1.978655e7, Pitch_ini=15.55, wg_nom=7.55, pg_nom=1.5e7):
        if libraryPath==library_rel_path:
            libraryPath = os.path.join(os.path.dirname(__file__), libraryPath)
            libDir = os.path.join(os.path.dirname(__file__),"..\\dependencies")

        super().__init__(libraryPath, inputFileName, max_time)
        self.sim_time = 0

        #Control variables
        self.Tem_ini = Tem_ini
        self.Pitch_ini = np.radians(Pitch_ini)
        self.wg_nom  = wg_nom
        self.pg_nom  = pg_nom


        """
        #1 action - pitch
         self.action_space = spaces.Box(
            low=-1,
            high=1,
            shape=(1,),
            dtype=np.float32
        )  

        #1 observation spaces_ wg    
        self.observation_space = spaces.Box(
            low=0,
            high=25,
            shape=(1,),
            dtype=np.float32
        ) 
        """

    def step(self,actions):
        #When start, run for 1sec without training
        while self.sim_time < 1:
            self.inp_array[4] = np.radians(18)
            self.inp_array[5] = np.radians(18)
            self.inp_array[6] = np.radians(18) 
            _error_status, _error_message = self.fast_update()
            self.sim_time = self.sim_time + self.dt.value
     
        #Simulate one FAST Step
        self.map_inputs(actions)        
        _error_status, _error_message = self.fast_update()     
        observation = self.map_outputs(self.output_values);         
        reward = self.reward(observation)
        terminate = self.do_terminate()
        if self.fatal_error(_error_status):   
            print(f"Warning {_error_status.value}: {_error_message.value}")
            terminate = True
            #If it fails, add the maximum reward it would have gotten, getting -1 in every step
            lost_rewards = (self.t_max.value-self.sim_time)/self.dt.value
            reward = reward - lost_rewards


        return observation, reward, terminate, {} #self.time      

    def reset(self):
        self.sim_time=0
        self.fast_deinit()
        self.fast_init()
        self.fast_start()
        self.inp_array[0] = self.Tem_ini
        self.inp_array[4] = self.Pitch_ini
        self.inp_array[5] = self.Pitch_ini
        self.inp_array[6] = self.Pitch_ini
        observation = self.map_outputs(self.output_values) 
        return observation       

    def do_terminate(self):
        terminate = False
        self.sim_time = self.sim_time + self.dt.value
        if (self.sim_time >= self.t_max.value-0.01) or self.end_early.value==True:
            terminate = True          
        return terminate

    def set_spaces(self, low_action, high_action, low_obs, high_obs):
        self.action_space = spaces.Box(
            low=low_action,
            high=high_action,
            dtype=np.float32
        )
        self.observation_space = spaces.Box(
            low=low_obs,
            high=high_obs,
            dtype=np.float32
        )
  ## Next functions should be re-implemented in the child class  
    def map_inputs(self,actions):
        #Pitch incremental inputs
        minPitch = np.radians(5)
        maxPitch = np.radians(30)

        pitch_deg = actions[0]*2*self.dt
        new_pitch = self.inp_array[4] + np.radians(actions[0])    
        new_pitch = np.clip(new_pitch, minPitch, maxPitch) #Clamp between min and max pitch
        self.inp_array[4] = new_pitch
        self.inp_array[5] = new_pitch
        self.inp_array[6] = new_pitch       

        return [new_pitch]
    
    def map_outputs(self, outputs):
        gym_obs = np.array(outputs[4], dtype=np.float32)       
        return gym_obs
 
    def reward(self,obs):
        reward = -(self.wg_nom-obs[3])**2 
        return reward
    
    