from naoqi import ALProxy
import time
import motion

robot_ip = "192.168.0.118"  # Inserisci l'indirizzo IP del robot
port=5010
motion = ALProxy("ALMotion", robot_ip, port)
tts = ALProxy("ALTextToSpeech", robot_ip, port)

motion.wakeUp()

# ANKLE
def ankle_circles():
    motion.setStiffnesses("RAnklePitch", 1.0)
    motion.setStiffnesses("RAnkleRoll", 1.0)
    motion.setAngles("RAnklePitch", 0.1, 0.5) # leggero sollevamento del piede
    time.sleep(1)

    for set_num in range(3):
        # Senso orario
        tts.say(f"Set {set_num + 1}, in senso orario")
        for i in range(10):
            motion.setAngles("RAnkleRoll", 0.2, 0.5)
            time.sleep(0.5)
            motion.setAngles("RAnkleRoll", -0.2, 0.5)
            time.sleep(0.5)
        tts.say("Ora in senso antiorario")
        for i in range(10):
            motion.setAngles("RAnkleRoll", -0.2, 0.5)
            time.sleep(0.5)
            motion.setAngles("RAnkleRoll", 0.2, 0.5)
            time.sleep(0.5)

    # Ritorno a posizione neutra
    motion.setAngles("RAnkleRoll", 0.0, 0.5)
    motion.setAngles("RAnklePitch", 0.0, 0.5)

    motion.wakeUp()

def single_leg_balance():
        for set_num in range(3):
            tts.say(f"Set {set_num + 1}, bilanciamento su una gamba")
            motion.setAngles("LHipPitch", -0.2, 0.3)  # solleva la sinistra
            time.sleep(0.5)
            motion.setStiffnesses("LHipPitch", 0.0)
            time.sleep(30)
            motion.setAngles("LHipPitch", 0.0, 0.3)
            time.sleep(0.5)

def eccentric_calf_raises_on_step():
    pass

def calf_stretching_on_step():
    pass

def plantar_mobilization():
    pass

# KNEE

def quadriceps_isometrics():
    pass

def low_step_ups():
    pass

def mini_squats():
    pass  # (0–45°)

def wall_squat():
    pass

def static_lunges():
    pass

def standing_quad_stretch():
    pass

def quad_set():
    pass  # see 2.1

# HAMSTRINGS_AND_CALVES

def isometric_contraction():
    pass

def calf_raises():
    pass

def standing_calf_stretch():
    pass

# SHOULDER_AND_ELBOW

# HIPS_CORE_AND_OTHERS

def isometric_hip_adduction():
    pass

def bird_dog():
    pass

def hip_bridge_on_bench():
    pass

def clamshell_side_lying():
    pass

def piriformis_stretch():
    pass

###############

def lateral_ankle_sprain():
    ankle_circles()
    single_leg_balance()

def achilles_tendinopathy():    
    eccentric_calf_raises_on_step()
    calf_stretching_on_step()
    plantar_mobilization()

def sprains_and_acl_tear():
    quadriceps_isometrics()
    low_step_ups()
    mini_squats()

def patellar_tendinopathy():
    wall_squat()
    static_lunges()
    standing_quad_stretch()

def meniscus_tear():
    quad_set()

def hamstring_strain():
    isometric_contraction()

def calf_strain():
    calf_raises()
    standing_calf_stretch()

#def shoulder_dislocation():
    
#def rotator_cuff_tendinopathy():
    
def groin_pull_or_adductor_tendinopathy():
    isometric_hip_adduction()

def lumbar_strain_and_spondylolysis():
    bird_dog()