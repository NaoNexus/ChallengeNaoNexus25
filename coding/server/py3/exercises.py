from naoqi import ALProxy
import time
import motion

robot_ip = "192.168.0.118"  # Inserisci l'indirizzo IP del robot
port=9559
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
    for set_num in range(3):
        tts.say(f"Set {set_num + 1} di calf raises")
        for rep in range(15):
            motion.setAngles("LAnklePitch", -0.3, 0.2)  # salita
            motion.setAngles("RAnklePitch", -0.3, 0.2)
            time.sleep(0.5)
            motion.setAngles("LAnklePitch", 0.1, 0.1)   # discesa
            motion.setAngles("RAnklePitch", 0.1, 0.1)
            time.sleep(0.5)
        motion.setAngles(["LAnklePitch", "RAnklePitch"], [0.0, 0.0], 0.2)
        time.sleep(1)

def plantar_mobilization():
    for set_num in range(3):
        tts.say(f"Set {set_num + 1}, mobilizzazione plantare")
        for rep in range(15):
            motion.setAngles(["LAnklePitch", "RAnklePitch"], [-0.1, -0.1], 0.2)  # punta
            time.sleep(0.3)
            motion.setAngles(["LAnklePitch", "RAnklePitch"], [0.1, 0.1], 0.2)   # tallone
            time.sleep(0.3)
        motion.setAngles(["LAnklePitch", "RAnklePitch"], [0.0, 0.0], 0.2)

# KNEE

def quadriceps_isometrics():
    for set_num in range(3):
        tts.say(f"Set {set_num + 1}, isometrici quadricipite")
        for rep in range(10):
            motion.setAngles(["LKneePitch", "RKneePitch"], [0.0, 0.0], 0.1)  # ginocchio esteso
            time.sleep(1)

def mini_squats():
    tts.say("Mini-squat, 3 serie da 12")
    for set_num in range(3):
        tts.say(f"Serie {set_num + 1}")
        for rep in range(12):
            # Piegamento (circa 45°)
            motion.setAngles(["LKneePitch", "RKneePitch"], [0.5, 0.5], 0.2)
            time.sleep(0.8)
            # Ritorno in posizione eretta
            motion.setAngles(["LKneePitch", "RKneePitch"], [0.0, 0.0], 0.2)
            time.sleep(0.8)

def static_lunges():
    tts.say("Static lunges, 3 serie da 10 per gamba")
    for set_num in range(3):
        tts.say(f"Serie {set_num + 1}")
        for leg in ["destra", "sinistra"]:
            tts.say(f"Gamba {leg}")
            for rep in range(10):
                if leg == "destra":
                    motion.setAngles("RKneePitch", 0.4, 0.2)  # Piegamento
                    time.sleep(0.5)
                    motion.setAngles("RKneePitch", 0.0, 0.2)  # Ritorno
                    time.sleep(0.5)
                else:
                    motion.setAngles("LKneePitch", 0.4, 0.2)
                    time.sleep(0.5)
                    motion.setAngles("LKneePitch", 0.0, 0.2)
                    time.sleep(0.5)


def quad_set():
    tts.say("Quad Set, 3 serie da 10 contrazioni")
    for set_num in range(3):
        tts.say(f"Serie {set_num + 1}")
        for rep in range(10):
            # Estensione ginocchia (contrazione)
            motion.setAngles(["RKneePitch", "LKneePitch"], [0.0, 0.0], 0.2)
            time.sleep(1.0)
            # Breve rilassamento
            motion.setAngles(["RKneePitch", "LKneePitch"], [0.1, 0.1], 0.2)
            time.sleep(0.5)


# HAMSTRINGS_AND_CALVES

def isometric_contraction():
    tts.say("Isometric contraction, 3 serie da 10")
    for set_num in range(3):
        tts.say(f"Serie {set_num + 1}")
        for rep in range(10):
            # Posizione semiflessa mantenuta brevemente
            motion.setAngles(["RKneePitch", "LKneePitch"], [0.3, 0.3], 0.2)
            time.sleep(2.0)
            # Ritorno a posizione eretta
            motion.setAngles(["RKneePitch", "LKneePitch"], [0.0, 0.0], 0.2)
            time.sleep(0.5)

def calf_raises():
    tts.say("Calf raises, 3 serie da 15")
    for set_num in range(3):
        tts.say(f"Serie {set_num + 1}")
        for rep in range(15):
            # Solleva i talloni (spinta in punta di piedi)
            motion.setAngles(["LAnklePitch", "RAnklePitch"], [-0.3, -0.3], 0.2)
            time.sleep(0.8)
            # Ritorno in posizione neutra
            motion.setAngles(["LAnklePitch", "RAnklePitch"], [0.0, 0.0], 0.2)
            time.sleep(0.8)


# HIPS_CORE_AND_OTHERS

def isometric_hip_adduction():
    tts.say("Isometric hip adduction, 3 serie da 15 contrazioni simulate")
    for set_num in range(3):
        tts.say(f"Serie {set_num + 1}")
        for rep in range(15):
            # Simula contrazione avvicinando le gambe
            motion.setAngles(["LHipRoll", "RHipRoll"], [-0.1, 0.1], 0.2)
            time.sleep(0.5)
            # Ritorno neutro
            motion.setAngles(["LHipRoll", "RHipRoll"], [0.0, 0.0], 0.2)
            time.sleep(0.5)


def bird_dog():
    tts.say("Bird-dog simulato, 3 serie da 10 per lato")
    for set_num in range(3):
        tts.say(f"Serie {set_num + 1}")
        for rep in range(10):
            # Lato destro (gamba sinistra e braccio destro)
            motion.setAngles(["LHipPitch", "RShoulderPitch"], [-0.3, -0.5], 0.2)
            time.sleep(1.0)
            motion.setAngles(["LHipPitch", "RShoulderPitch"], [0.0, 1.5], 0.2)
            time.sleep(0.5)

            # Lato sinistro (gamba destra e braccio sinistro)
            motion.setAngles(["RHipPitch", "LShoulderPitch"], [-0.3, -0.5], 0.2)
            time.sleep(1.0)
            motion.setAngles(["RHipPitch", "LShoulderPitch"], [0.0, 1.5], 0.2)
            time.sleep(0.5)

###############

def lateral_ankle_sprain():
    ankle_circles()
    single_leg_balance()


def achilles_tendinopathy():    
    eccentric_calf_raises_on_step()
    plantar_mobilization()

def sprains_and_acl_tear():
    quadriceps_isometrics()
    mini_squats()

def patellar_tendinopathy():
    static_lunges()

def meniscus_tear():
    quad_set()

def hamstring_strain():
    isometric_contraction()

def calf_strain():
    calf_raises()
   
def groin_pull_or_adductor_tendinopathy():
    isometric_hip_adduction()

def lumbar_strain_and_spondylolysis():
    bird_dog()
