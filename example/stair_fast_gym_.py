import numpy as np
import utils
from src.openfast_gym.fast_gym_8 import FastGym_8
import pandas as pd

#Parameters
library_path = "C:\dev_local_repo\TFM_WS\openfast-gym\dependencies\openfastlib.dll"
input_file_name = "C:\dev_local_repo\TFM_WS\openfast-gym\FAST_cfg\IEA-15-240-RWT-Monopile.fst"
MAX_T = 200


def pitch_stair_increment(ts,pitch_pre):
    if ts<40:
        pitch_ctrl = 0
    elif ts<80:
        if pitch_pre<np.pi/4:
            pitch_ctrl = 1
        else:
            pitch_ctrl = 0
    elif ts<120:
        if pitch_pre<np.pi/3:
            pitch_ctrl = 1
        else:
            pitch_ctrl = 0
    elif ts<160:
        if pitch_pre<np.pi/2:
            pitch_ctrl = 1
        else:
            pitch_ctrl = 0
    else:
        pitch_ctrl = 0
    return pitch_ctrl 


if __name__ == "__main__":
    Pg_nom = 15000 #kw
    wg_nom = 0.79 #rad/s = 7.55rpm
    Tem_ini = 3000e3 #Nm
    Pitch_ini = 0.27 #rad = 15.55deg
    e_int = 0
    observation=[0.0,0.0,0.0,0.0]
    actions = [0,0]
    terminated=False

    env = FastGym_8(inputFileName=input_file_name, libraryPath=library_path,  max_time=MAX_T)
    observation = env.reset()

    while (terminated==False):
        error=observation[0]
        #actions[0] = pitch_pi(e=error,Kp=0.12,Ki=0.0008,pitch_ini=Pitch_ini) 
        pitch_pre = observation[3]
        pitch_ctrl = pitch_stair_increment(env.sim_time,pitch_pre)
        actions[0] = pitch_ctrl
        actions[1] = Tem_ini    #Torque in Nm     
        try:
            observation, reward, terminated, _ = env.step(actions)
        except:
            print("Error performing step ")
            terminated=True
            break
        

    utils.log_and_exit(env.myLog,"stair_OpenFastGym_8")

        
        