#/usr/bin/env python3

#!coding:utf-8
import threading
import os,time,random,socket, ast, math
from queue import Queue


class Producer(threading.Thread):
    
    def __init__(self, t_name, queue1, queue3):
        threading.Thread.__init__(self, name=t_name)
        self.data = queue1
        self.change = queue3
        
    
    def run(self):
        UDP_IP = "127.0.0.1"
        UDP_PORT1 = 5000        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((UDP_IP, UDP_PORT1))        
        while True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            #print ("received message:", data)
            message = data.decode('utf-8')
            a = ast.literal_eval(message)
            #print(type(a))
            #print("receive message",a)
            if a[0]=='carinfo':
                self.data.put(a)
            elif a[0]=='stop':
                print("stop:", a)
                self.change.put(a)



class Sender(threading.Thread):

    def __init__(self, t_name, queue2):
        threading.Thread.__init__(self, name=t_name)
        self.data = queue2
        #stop sign for approaches
        
    def run(self):
       # print("start")
    	while True:
            data=[]
            UDP_IP = "127.0.0.1"
            UDP_PORT1 = 4000    #send to wsm-channel then forward to DSRC-2
            UDP_PORT2 = 6000    #send to collision observer
            data=self.data.get()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            if data[0]=='sent':
                MESSAGE = str.encode(str(data))
                print ("send message:", MESSAGE)
                sock.sendto(MESSAGE, (UDP_IP, UDP_PORT1))
            
            elif data[0]=='cross':
                lane = data[3]
                pos = data[5]
                if lane == 1:
                    twoD = [-pos, -2]
                elif lane == 2:
                    twoD = [pos, 2]
                elif lane == 3:
                    twoD = [-2, pos]
                else:
                    twoD = [2, -pos]
                data[5] = twoD
                MESSAGE = str.encode(str(data))
                print ("send cross: ", MESSAGE)
                sock.sendto(MESSAGE, (UDP_IP, UDP_PORT2))
            #sock.sendto(MESSAGE, (UDP_IP, UDP_PORT2))


class Observer(threading.Thread):
    """
    Consumer thread 
    """
    def __init__(self, t_name, queue1, queue2, queue3):
        threading.Thread.__init__(self, name=t_name)
        self.data = queue1
        self.send = queue2
        self.change = queue3
        self.carlist = []
        self.changelist = []
        #stop sign for approaches
        
    def run(self):
        while True:
            while self.data.qsize():
                val = self.data.get()
                self.carlist.append(val)
            while self.change.qsize():
            	val = self.change.get()
            	self.changelist.append(val)
            self.update_change()
            self.update_position()
            self.calculate_distance()

                    
            time.sleep(0.1) 	    


    def update_change(self):
   		cnt = len(self.changelist)
   		for j in self.changelist:
   			for i in self.carlist:
   				if i[1]==j[1]:
   					arrival = j[9]
   					speed = i[7]
   					acc = - speed/(arrival-i[2])
   					i[8] = acc
   					i[9]=arrival
   					i[0]='stop'
   		self.changelist.clear()





    def update_position(self):
        #0-source, 1-id, 2-timestamp, 3-lane, 4-movement, 5-absolute value of position, 6-length, 7-speed, 8-accelaration
        passing_distance=0
        new_speed=0
        new_pos=0
        t=time.time()
        for val in self.carlist:
            passing_distance = val[7]*(t-val[2]) + 1.0/2*val[8]*(t-val[2])*(t-val[2])
            new_speed = val[7] + (t-val[2])*val[8] 
            val[2]=t
            new_pos = val[5] - passing_distance
            if new_pos<0 or new_pos>50:
                self.carlist.remove(val)
            lane = val[3]
            val[7] = new_speed
            val[5] = new_pos
            if val[0]=='stop':
                if new_speed <= 0:
                    new_speed = 0
                    val[8] = 0
                    new_pos = 4
                    if val[2]>=val[9]:
                        val[5]=new_pos
                        val[7] = 8.0
                        val[0] = 'cross'
                        self.carlist.remove(val)
                        self.send.put(val)
            	
            
            elif val[0]=='sent' and new_pos <= 4 and val[2]>val[9]:              
                val[0] = 'cross'
                self.carlist.remove(val)
                self.send.put(val)




    def calculate_distance(self):
        total_count = len(self.carlist)
        for i in range(total_count-1):
            for j in range(i+1,total_count):
                if self.carlist[i][3]==self.carlist[j][3]:
                    pos_i = self.carlist[i][5]
                    pos_j = self.carlist[j][5]
                    distance = pos_i - pos_j
                    if (distance * pos_i) < 0:
                	# i is front car, j is back car
                        tmp = abs(distance) -  2*self.carlist[j][7]
                       # tmp2 = abs(distance) - 4 * self.carlist[j][6]
                        if tmp < 0:
                            self.carlist[j][0] = 'carinfo'
                            self.carlist[j][7] = self.carlist[j][7]/3.0*2.0
                            
                            self.carlist[j][8] = 0
                            #self.send.put(self.carlist[j])

                    else:
            		# i is back car
                        tmp = abs(distance) -  2*self.carlist[i][7]
                        #tmp2 = abs(distance) - 4 * self.carlist[i][6]
                        if tmp < 0:
                            self.carlist[j][0] = 'carinfo'
                            self.carlist[i][7] = self.carlist[j][7]/3.0*2.0
                            self.carlist[i][8] = 0
                           # self.send.put(self.carlist[i])
        for x in self.carlist:
            if x[0]=='carinfo':
                x[0]='sent'
                x[8]==0
                self.send.put(x)





             

def main():
    """

    """
    queue1 = Queue() 
    queue2 = Queue()  
    queue3 = Queue()
    sender = Sender('send', queue2)
    producer = Producer('Pro.', queue1, queue3)  
    observer = Observer('Obs.', queue1, queue2, queue3) 
    sender.start()
    producer.start()  
    observer.start() 
    sender.join()
    producer.join()
    observer.join()
    #print('All threads terminate!')



if __name__ == '__main__':
    main()




