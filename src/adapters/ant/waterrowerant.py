from os import _exit
from time import sleep

from . import antdongle as ant
from . import antfe as fe

from collections import deque

def main(out_q, ant_in_q):
    global out_q_hr
    out_q_hr = out_q
    EventCounter = 0
    messages = []       # messages to be sent to
    Antdongle = ant.clsAntDongle() # define the ANt+ dongle
    print(Antdongle.Message)
    if not Antdongle.OK:
        print("ANT+ dongle not ready, exiting...")
        _exit(-1)
    Antdongle.Calibrate()   # reset the dongle and defines it as node
    sleep(0.25)
    Antdongle.Trainer_ChannelConfig() # define the channel needed for fitness equipements
    sleep(0.25)
    Antdongle.SlaveHRM_ChannelConfig(0) #20252
    sleep(0.25)

    Waterrower = fe.antFE(Antdongle) # hand over the class to antfe to give acces to the dongle

    while True:
        if len(ant_in_q) != 0: #as long as the deque data from WR are not empty
            WaterrowerValuesRaw = ant_in_q.pop() # remove it from the deque and put in variable

            if EventCounter < 255:  # This is important as after 256 message the counter must set to zero as a rollover occures for ant+ data
                Waterrower.EventCounter = EventCounter # set the eventcounter of the instance
                Waterrower.BroadcastTrainerDataMessage(WaterrowerValuesRaw) # insert data into instance
                messages.append(Waterrower.fedata) # depending on the event counter value load the message arrey with the either Fitness equipement, rowerdata, manu data or product data
                if len(messages) > 0:
                    Antdongle.Write(messages, False, False) # check if length of array is greater than 0 if yes then send data over Ant+
                EventCounter += 1
                #print(EventCounter)
                messages = []
                events = Antdongle.Read(False)
                for evt in events:
                    synch, length, id, info, checksum, _rest, Channel, DataPageNumber = Antdongle.DecomposeMessage(evt)
                    if id == Antdongle.msgID_BroadcastData:
                        if Channel == Antdongle.channel_HRM_s:
                            if DataPageNumber & 0x7f in (0,1,2,3,4,5,6,7,89):
                                Channel, DataPageNumber, Spec1, Spec2, Spec3, HeartBeatEventTime, HeartBeatCount, HRM_HeartRate = Antdongle.msgUnpage_Hrm(info)
                                #print("hr: %d" % HRM_HeartRate)
                                out_q_hr.put("hr %d" % HRM_HeartRate)
            else:
                 EventCounter = 0
                 messages = []
        else:
            pass

        sleep(0.25) # Ant+ defines to send a message every 25 ms
                

def FakeRower(WRValues_test):
    WRValues_test_updated = {}
    WRValues_test_updated.update({'stroke_rate': 23})
    WRValues_test_updated.update({'total_strokes': WRValues_test['total_strokes'] + 1})
    WRValues_test_updated.update({'total_distance_m': WRValues_test['total_distance_m'] + 1})
    WRValues_test_updated.update({'speed': 500000 })
    WRValues_test_updated.update({'watts': 150})
    WRValues_test_updated.update({'total_kcal': WRValues_test['total_kcal'] + 1})
    WRValues_test_updated.update({'elapsedtime': WRValues_test['elapsedtime'] +1})
    return WRValues_test_updated

if __name__ == '__main__':

    # WRValues_test = {
    #             'stroke_rate': 23,
    #             'total_strokes': 10,
    #             'total_distance_m': 10,
    #             'instantaneous pace': 0,
    #             'speed': 10,
    #             'watts': 50,
    #             'total_kcal': 0,
    #             'total_kcal_hour': 0,
    #             'total_kcal_min': 0,
    #             'heart_rate': 120,
    #             'elapsedtime': 25,
    #         }
    main()