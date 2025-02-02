import numpy as np
import utils
from src.openfast_gym.fast_gym_8 import FastGym_8
import pandas as pd

#Parameters
library_path = "C:\dev_local_repo\TFM_WS\openfast-gym\dependencies\openfastlib.dll"
input_file_name = "C:\dev_local_repo\TFM_WS\openfast-gym\FAST_cfg\IEA-15-240-RWT-Monopile.fst"
MAX_T = 10

Pg_nom = 15000 #kw
wg_nom = 7.56 #rpm
Tem_ini = 3000e3 #Nm
Pitch_ini = 15.55 #deg
e_int = 0


def pitch_pi(e,Kp,Ki,pitch_ini=15.55):
    global e_int
    e_int = e_int + e
    #PID controller
    pitch_pid = Kp*e + Ki*e_int
    pitch = (-pitch_pid*180/np.pi + pitch_ini)
    pitch = np.clip(pitch,-30,30)

    return pitch

def rate_limiter(u,u_ant,rate):
    delta_u = u - u_ant
    u = np.clip(u, u-rate, u+rate)
    return u


if __name__ == "__main__":
    env = FastGym_8(inputFileName=input_file_name, libraryPath=library_path,  max_time=MAX_T)
    env.reset()
    
    #Init variables
    e_int = 0
    observation=[0.0,0.0,0.0,0.0]
    actions = [0,0]
    terminated=False

    while (terminated==False):
        error=observation[0]
        actions[0] = pitch_pi(e=error,Kp=0.12,Ki=0.0008,pitch_ini=Pitch_ini) 
        actions[1] = Tem_ini    #Torque in Nm   
        
        try:
            observation, reward, terminated, _ = env.step(actions)
        except:
            print("Error performing step ")
            terminated=True
            break
        

    utils.log_and_exit(env.myLog,"OpenFastGym_8")

        
        