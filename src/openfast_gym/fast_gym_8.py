from openfast_gym.fast_gym_base import FastGymBase
import numpy as np
import socket
import json
    

input_file_name = "C:\\dev_local_repo\\WTRL\\fast_gym\\fast_gym\\dependencies\\FAST_1\\IEA-15-240-RWT-Monopile.fst"
library_rel_path = "..\\dependencies\\openfastlib.dll"

"""
Action: Pitch increment (normalized [-1,1]) (+Pitch_ref)
Observations: GenSpeed error [rad/s], Pitch [rad], Wind Speed x [12,13] [m/s], Pitch_ref [rad]
Rewards: -K1*speed_error^2 - K2*Integral(speed_error^2)
Wind modified in each episode
"""
class FastGym_8(FastGymBase):
    def __init__(self, inputFileName=input_file_name, libraryPath=library_rel_path, max_time=40, Tem_ini=1.978655e7, Pitch_ini=0.27, wg_nom=0.79, pg_nom=1.5e7,enable_myLog=1):
        super().__init__(inputFileName, libraryPath, max_time, Tem_ini, Pitch_ini, wg_nom, pg_nom)
        
         #GYM API DEFINITION
        low_action = np.array([-1], dtype=np.float32)
        high_action = np.array([1], dtype=np.float32)  
        #low_obs = np.array([-10,0,0], dtype=np.float32)
        #high_obs = np.array([10,90,40], dtype=np.float32)
        low_obs = np.array([-10,0,12,0], dtype=np.float32)
        high_obs = np.array([10,np.pi/2,13,np.pi/2], dtype=np.float32)
        super().set_spaces(low_action, high_action, low_obs, high_obs)

        #Init internal variables
        self.actions=[0]
        self.pitch_ref = Pitch_ini

        #LOGS
        self.enable_myLog = enable_myLog
        self.myLog = []
        
    def map_inputs(self,actions):
        self.actions=actions
        norm_delta_pitch = actions[0]
        
        minPitch = np.radians(0)
        maxPitch = np.radians(90)
        self.control_time_step = 0.2
        pitch_ref = self.pitch_ref

        self.pitch_increment = norm_delta_pitch*np.radians(5)*self.control_time_step # [rad] Norm 1 = 5 deg/s
        new_pitch = pitch_ref + self.pitch_increment   
        new_pitch = np.clip(new_pitch, minPitch, maxPitch) #Clamp between min and max pitch
        self.pitch_ref = new_pitch

        #FAST INPUTS
        self.inp_array[4] = new_pitch
        self.inp_array[5] = new_pitch
        self.inp_array[6] = new_pitch       

        return [new_pitch]

    def map_outputs(self, outputs):
        wg = (outputs[4]*2*np.pi)/60
        error_wg = self.wg_nom-wg
        pitch = np.radians(outputs[3])
        Vx = outputs[1]
        pitch_ref = self.pitch_ref
        gym_obs=[error_wg,pitch,Vx,pitch_ref] 
        self.obs = gym_obs  
        return gym_obs
   
    def reward(self,obs):
        reward = -(obs[0])**2 
        self.instant_reward = reward
        self.log_callback()
        return reward
    
    def reset(self):
        self.sim_time=0
        self.fast_deinit()
        self.fast_init()
        self.fast_start()
        self.inp_array[0] = self.Tem_ini
        self.inp_array[4] = self.Pitch_ini
        self.inp_array[5] = self.Pitch_ini
        self.inp_array[6] = self.Pitch_ini
        obs = self.map_outputs(self.output_values)
        
        #obs = self.run_burn_in()
        return obs
    
    def run_burn_in(self):
        while self.sim_time < self.init_time_actions:
            obs, *_ = self.step([0])
        return obs
 
    def log_callback(self):
            if self.enable_myLog:
                self.myLog.append({
                    "time": self.sim_time,
                    "Pitch_increment": self.actions[0],
                    "w_rpm":self.output_values[4],
                    "w_rads":self.output_values[4]*2*np.pi/60,
                    "pitch": self.output_values[3],
                    "pitch_ref": self.pitch_ref,
                    "Vx": float(self.output_values[1]),
                    "obs.error_wg": self.obs[0],
                    "obs.pitch": self.obs[1],
                    "obs.Vx": self.obs[2],
                    "obs.pitch_ref": self.obs[3],
                    "reward": self.instant_reward
                })