#import cwdpath
import numpy as np
from src.openfast_gym.openfast_gym_env import OpenFastEnv
import pandas as pd
#import beepy

#Parameters
library_path = "C:\\dev_local_repo\\openfast-gym\\dependencies\\openfastlib.dll"
input_file_name = "C:\\dev_local_repo\\openfast-gym\\example\\FAST_cfg\\IEA-15-240-RWT-Monopile.fst"
MAX_T = 10

Pg_nom = 15000 #kw
wg_nom = 7.56 #rpm
Tem_ini = 3000e3 #Nm
Pitch_ini = 15.55 #deg
e_int = 0

    
def name_from_date():
    from datetime import datetime
    now = datetime.now()
    date_time = now.strftime("%m_%d_%Y_%H_%M_%S")
    file_name = "output/data_" + date_time + ".csv"
    return file_name

def save_results(observations,actions,file_name=name_from_date()):
    observations_df = pd.DataFrame(observations)
    actions_df = pd.DataFrame(actions)
    frames = [observations_df, actions_df]
    result = pd.concat(frames, axis=1)
    result.to_csv(file_name, sep=',', encoding='utf-8')

def pitch_pi(Ref_wg,wg,Kp,Ki,pitch_ini=15.55):
    #PI controller for pitch
    #Ref_wg is the reference rotor speed
    #wg is the current rotor speed
    #Kp, Ki are the PID gains

    #Error
    e = (Ref_wg-wg)*2*np.pi/60
    #Integral
    global e_int
    e_int = e_int + e
    #PID controller
    pitch_pid = Kp*e + Ki*e_int
    pitch = (-pitch_pid*180/np.pi + pitch_ini)
    if pitch > 30:
        pitch = 30
    elif pitch < 0:
        pitch = 0

    return pitch

def rate_limiter(u,u_ant,rate):
    #Rate limiter
    #u is the input
    #u_ant is the previous input
    #rate is the maximum rate of change
    delta_u = u - u_ant
    if delta_u > rate:
        u = u_ant + rate
    elif delta_u < -rate:
        u = u_ant - rate
    return u


if __name__ == "__main__":
    env = OpenFastEnv(library_path, input_file_name, MAX_T,Tem_ini,Pitch_ini)
    env.reset()
    #Init variables
    e_int = 0
    pitch_pre = Pitch_ini
    observations = []
    actions = []
    wg = wg_nom

    terminated=False
    i = 0
    while (terminated==False):
        #Declare Dictionary action with fields Tq and pitch
        action = {}
        action["Tq"] = Tem_ini    #Torque in Nm
        action["pitch"] = pitch_pi(Ref_wg=wg_nom,wg=wg,Kp=0.2,Ki=0.001,pitch_ini=Pitch_ini)    
        
        try:
            action_arr = env.action_from_dict(action)
            observation, reward, terminated, extra = env.step_abs_actions(action_arr)
            obs_dict = env.obs_to_dict(observation)
        except:
            print("Error performing step")
            terminated=True
            break

        wg = obs_dict["GenSpeed"]

        #Log data every 10 steps
        if i % 10 == 0:
            observations.append(obs_dict)
            actions.append(action)
        i+=1
        if terminated:
            print("Terminated")
            break

    #Write observations and actions to file in CSV  
    save_results(observations,actions)

        
        