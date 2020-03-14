from Globals import *

def isTeamBTrue(self):
    if (TEAM_NAME[1] == "Red" or RED_MULTIPLIER == 1.15) and RED_MULTIPLIER != 1.0:
        return True
    else:
        return False