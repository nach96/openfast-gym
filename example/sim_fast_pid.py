import numpy as np
import pandas as pd
import sys
import os
current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_dir, "..\\src\\openfast_gym"))
from fast_gym_base import FastGymBase

#Parameters
library_path = "C:\\dev_local_repo\\Cristian_Python_OpenFast\\dependencies\\openfastlib.dll"
input_file_name = "C:\\dev_local_repo\\Cristian_Python_OpenFast\\FAST_cfg\\IEA-15-240-RWT-Monopile.fst"
MAX_T = 40

Pg_nom = 15000 #kw
wg_nom = 7.56 #rpm
Tem_ini = 3000e3 #Nm
Pitch_ini = 15.55 #deg
e_int = 0

    
def name_from_date():
    from datetime import datetime
    now = datetime.now()
    date_time = now.strftime("%m_%d_%Y_%H_%M_%S")
    file_name = "data_" + date_time + ".csv"
    #file_name = "data_" + date_time + ".csv"
    return file_name

def save_results(observations,actions,file_name=name_from_date()):
    observations_df = pd.DataFrame(observations)
    actions_df = pd.DataFrame(actions)
    frames = [observations_df, actions_df]
    result = pd.concat(frames, axis=1)
    result.to_csv(file_name, sep=',', encoding='utf-8')

def pitch_pi(e,Kp,Ki,pitch_ini=15.55):
    #PI controller for pitch
    #Ref_wg is the reference rotor speed
    #wg is the current rotor speed
    #Kp, Ki are the PID gains

    #Error
    #e = (Ref_wg-wg)*2*np.pi/60
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
    #Python OpenFast
    env = FastGymBase(inputFileName=input_file_name, libraryPath=library_path,  max_time=MAX_T,Tem_ini=Tem_ini,Pitch_ini=Pitch_ini)
    env.reset()
    #Init variables
    e_int = 0
    pitch_pre = Pitch_ini
    wg = wg_nom
    observation=[0,0,0]
    actions = [0,0]
    #Log variables
    obs_dict = {}
    act_dict = {}
    log_observations = []
    log_actions = []

    terminated=False
    i = 0

    while (terminated==False):
        error=observation[0]
        actions[0] = pitch_pi(e=error,Kp=0.12,Ki=0.0008,pitch_ini=Pitch_ini) 
        actions[1] = Tem_ini    #Torque in Nm   
        
        try:
            observation, reward, terminated, others = env.step(actions)
        except:
            print("Error performing step")
            terminated=True
            break
        
        #Log data every 10 steps
        if i % 10 == 0:
            obs_dict["error"] = observation[0]
            obs_dict["Pitch"] = observation[1]
            obs_dict["Vx"] = observation[2]
            act_dict["Pitch_cmd"] = actions[0]
            act_dict["Tem_cmd"] = actions[1]
            log_observations.append(obs_dict.copy())
            log_actions.append(act_dict.copy())
        i+=1
        if terminated:
            print("Terminated")
            break
        
    #Write observations and actions to file in CSV  
    save_results(log_observations,log_actions)

        
        