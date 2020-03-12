#/usr/bin/env python3

#!coding:utf-8
import threading
import os,time,random,socket, math, ast
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


    def run(self):
        UDP_IP = "127.0.0.1"
        UDP_PORT1 = 6000        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((UDP_IP, UDP_PORT1))        
        while True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            #print ("received message:", data)
            message = data.decode('utf-8')
            a = ast.literal_eval(message)
            if a[0]=='cross':
            #print(type(a))
                #print("receive:",a)
                self.data.put (a)  

class Consumer(threading.Thread):
    """
    Consumer thread 
    """
    def __init__(self, t_name, queue):
        threading.Thread.__init__(self, name=t_name)
        self.data = queue
        self.carlist = []

    def run(self):
        while True:
            while self.data.qsize():
                val = self.data.get()
                val[8]=0
                self.carlist.append(val)
                print("cars in the intersection: \n", len(self.carlist))
            self.update_position()
            self.calculate_distance()
            #time.sleep(0.1) 

    def update_position(self):
    #    if self.carlist.qsize()>0:
        t=time.time()
      #      if (t-self.time)>5:
       #         tmp = ['clean']
        #        self.send.put(tmp)
         #   self.time = t




        for val in self.carlist:
            
            distance = val[7]*(t-val[2])
            movement = val[4]
            old_position = val[5]
        #0-source, 1-id, 2-timestamp, 3-lane, 4-movement, 5-position, 6-length, 7-speed, 8-accelaration
            if movement ==1:
                new_position = [old_position[0]+distance,old_position[1]]
            elif movement ==4:
                new_position = [old_position[0]-distance,old_position[1]]
            elif movement == 8:
                new_position = [old_position[0], old_position[1]-distance]
            elif movement == 11:
                new_position = [old_position[0], old_position[1]+distance]
            elif movement == 3:
                new_position = [old_position[0]+distance/math.sqrt(2),old_position[1]-distance/math.sqrt(2)]
            elif movement == 5:
                new_position = [old_position[0]-distance/math.sqrt(2),old_position[1]+distance/math.sqrt(2)]
            elif movement == 9:
                new_position = [old_position[0]-distance/math.sqrt(2),old_position[1]-distance/math.sqrt(2)]
            elif movement == 10:
                new_position = [old_position[0]+distance/math.sqrt(2),old_position[1]+distance/math.sqrt(2)]
            elif movement == 2:
                new_position = [old_position[0]+distance/math.sqrt(2),old_position[1]+distance/math.sqrt(2)]
            elif movement == 6:
                new_position = [old_position[0]-distance/math.sqrt(2),old_position[1]-distance/math.sqrt(2)]
            elif movement == 7:
                new_position = [old_position[0]+distance/math.sqrt(2),old_position[1]-distance/math.sqrt(2)]
            else:
                new_position = [old_position[0]-distance/math.sqrt(2),old_position[1]+distance/math.sqrt(2)]
            val[2] = t
            val[5] = new_position
            judgement = max(abs(new_position[0]), abs(new_position[1]))
            if judgement>4.1:
                #out of intersection
                self.carlist.remove(val)

    def calculate_distance(self):
        total_count = len(self.carlist)
        for i in range(total_count-1):
            for j in range(i+1,total_count):
                distance = math.sqrt(sum([(i-j)**2 for (i,j) in zip(self.carlist[i][5],self.carlist[j][5])]))
                if (distance < 2) and (self.carlist[i][3]!=self.carlist[j][3]):
                    print("car %s: %s and car %s: %s collide" % (self.carlist[i][1], self.carlist[i][5], self.carlist[j][1], self.carlist[j][5]))





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


if __name__ == '__main__':
    main()


