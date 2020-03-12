#/usr/bin/env python3

#!coding:utf-8
import threading
import os,time,random,socket, ast, math
from queue import Queue

#distance between traffic controller and initial position: 50m
#lane: 4m


class Producer(threading.Thread):
    """
    Producer thread 
    """
    def __init__(self, t_name, queue):  
        threading.Thread.__init__(self, name=t_name)  
        # total cars in simulation
        self.data = queue
        self.maxcar = 100


    def run(self):
        for i in range(self.maxcar):  
            #decide which kind of car
            temptime = time.time()
            lane = random.randint(1,4)
            movement = lane * 3 - random.randint(0,2)
            pos = 50
            self.data.put(['carinfo',i,temptime,lane, movement, pos,random.uniform(3.0, 5.0), random.uniform(10.0, 13.0), 0,0,0,[]])
            #0-source, 1-id, 2-timestamp, 3-lane, 4-movement, 5-absolute value of position, 6-length, 7-speed, 8-accelaration
            print("%s: car %s is comming to the intersection!" % (temptime, i))  # 当前时间t生成编号d并加入队列
             # sleep some time before next car
            time.sleep(2)  

class Consumer(threading.Thread):
    """
    Consumer thread 
    """
    def __init__(self, t_name, queue):
        threading.Thread.__init__(self, name=t_name)
        self.data = queue
        self.maxcar = 100
        #stop sign for approaches
        
    def run(self):
       # print("start")
    	while True:
            
            UDP_IP = "127.0.0.1"
            UDP_PORT1 = 4000    #send to wsm-channel then forward to DSRC-2
            UDP_PORT2 = 5000    #send to speed adjustment
            MESSAGE = str.encode(str(self.data.get()))
            
            #print ("UDP target IP:", UDP_IP)
            #print ("UDP target port:", UDP_PORT)
            print ("message:", MESSAGE)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
           # sock.sendto(MESSAGE, (UDP_IP, UDP_PORT1))
            sock.sendto(MESSAGE, (UDP_IP, UDP_PORT2))
        #print("end")




def main():
    """

    """
    queue = Queue()  
    producer = Producer('Pro.', queue)  
    consumer = Consumer('Con.', queue)  
    producer.start()  
    consumer.start()  

    producer.join()
    consumer.join()
    print('All threads terminate!')



if __name__ == '__main__':
    main()


