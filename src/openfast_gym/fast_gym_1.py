from openfast_gym.fast_gym_base import FastGymBase
import numpy as np
import socket
import json
    

input_file_name = "C:\\dev_local_repo\\WTRL\\fast_gym\\fast_gym\\dependencies\\FAST_1\\IEA-15-240-RWT-Monopile.fst"
library_rel_path = "..\\dependencies\\openfastlib.dll"
class FastGym_1(FastGymBase):
    """ FastGym_1 environment
    - Actions: Pitch increment
    - Observations: GenSpeed error, Pitch, Wind Speed x
    - Reward: -(GenSpeed error)^2
    """
    def __init__(self, inputFileName=input_file_name, libraryPath=library_rel_path, max_time=40, Tem_ini=1.978655e7, Pitch_ini=15.55, wg_nom=7.55, pg_nom=1.5e7,enable_myLog=1,myLogName=""):
        super().__init__(inputFileName, libraryPath, max_time, Tem_ini, Pitch_ini, wg_nom, pg_nom)
        
        # SPACES -isnt there a cleaner way to set action spaces in the child class?
        low_action = np.array([-1], dtype=np.float32)
        high_action = np.array([1], dtype=np.float32)  
        low_obs = np.array([-10,0,0], dtype=np.float32)
        high_obs = np.array([10,90,40], dtype=np.float32)
        super().set_spaces(low_action, high_action, low_obs, high_obs)

        #Init internal variables
        self.actions=[0]


        #LOGS
        self.enable_myLog = enable_myLog
        self.myLog = []
        self.myLogName = myLogName

        #UDP client
        self.sock = socket.socket(socket.AF_INET, # Internet
                    socket.SOCK_DGRAM) # UDP
        
    def map_inputs(self,actions):
        self.actions=actions
        #Pitch incremental inputs
        minPitch = np.radians(5)
        maxPitch = np.radians(45)

        pitch_deg = actions[0]*2*self.dt.value # Max 2 deg/s
        new_pitch = self.inp_array[4] + np.radians(pitch_deg)    
        new_pitch = np.clip(new_pitch, minPitch, maxPitch) #Clamp between min and max pitch
        self.inp_array[4] = new_pitch
        self.inp_array[5] = new_pitch
        self.inp_array[6] = new_pitch       

        return [new_pitch]

    def map_outputs(self, outputs):
        wg = outputs[4]
        error_wg = self.wg_nom-wg
        pitch = outputs[3]
        Vx = outputs[1] 
        gym_obs=[error_wg,pitch,Vx]   
        return gym_obs
   
    def reward(self,obs):
        reward = -(obs[0])**2 
        self.log_callback(reward)
        self.udp_callback(reward)
        return reward
    
    def log_callback(self,reward):
        #log actions and observations
        #log one out of 10 samples
        if self.enable_myLog:
            if self.sim_time % 0.1 < 0.01:
                self.myLog.append({"time":self.sim_time,"pitch":self.output_values[3],"wg":self.output_values[4],"Vx":float(self.output_values[1]),"Pitch increment":self.actions[0],"reward":reward})
    
    def udp_callback(self,reward):
        if self.enable_myLog:
            if self.sim_time % 0.1 < 0.01:
                name = self.myLogName + "_training_data"
                data = {
                    name: {
                        "time":float(self.sim_time),
                        "pitch":float(self.output_values[3]),
                        "wg":float(self.output_values[4]),
                        "wg_error":float(self.wg_nom-self.output_values[4]),
                        "Vx":float(self.output_values[1]),
                        "Pitch increment":float(self.actions[0]),
                        "reward":float(reward)
                    }
                }
                self.sock.sendto( json.dumps(data).encode(), ("127.0.0.1", 9870) )
