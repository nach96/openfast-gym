from simpleWT_gym.simple_wt_gym import SimpleWtGym
import numpy as np
import logging

class FastGym_4(SimpleWtGym):
    def __init__(self, inputFileName="", libraryPath="", max_time=40, Tem_ini=1.978655e7, Pitch_ini=15.55, wg_nom=7.55, pg_nom=1.5e7,enable_myLog=1,myLogName=""):
        logging.debug("fast_gym_4, wrapper of SimpleWTGym Initialized")
        wg_nom_rad = wg_nom*(2*np.pi)/60
        super().__init__(t_max=max_time, wg_nom=wg_nom_rad)