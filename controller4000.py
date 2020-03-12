#/usr/bin/env python3

import socket
import threading
import os,time,random,ast, math
from queue import Queue



class Receiver(threading.Thread):
    
    def __init__(self, t_name, queue):
        threading.Thread.__init__(self, name=t_name)
        self.data = queue
        
    
    def run(self):
        UDP_IP = "127.0.0.1"
        UDP_PORT1 = 4000        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((UDP_IP, UDP_PORT1))        
        while True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            #print ("received message:", data)
            message = data.decode('utf-8')
            a = ast.literal_eval(message)
            #print(type(a))
            if a[0]=='sent':
            	#print ("message:", a)
            	self.data.put (a)
                #self.data.put(a)


class Sender(threading.Thread):
    """
   
    """
    def __init__(self, t_name, controlinfo):
        threading.Thread.__init__(self, name=t_name)
        self.send = controlinfo
        
        
    def run(self):
       # print("start")
    	while True:
            
            UDP_IP = "127.0.0.1"
            UDP_PORT2 = 5000    #send to wsm-channel then forward to DSRC-1
            MESSAGE = str.encode(str(self.send.get()))
            
            #print ("UDP target IP:", UDP_IP)
            #print ("UDP target port:", UDP_PORT)
            #print ("message:", MESSAGE)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.sendto(MESSAGE, (UDP_IP, UDP_PORT2))


class Cal(threading.Thread):
    def __init__(self, t_name, queue, controlinfo):
        threading.Thread.__init__(self, name=t_name)
        self.data = queue
        self.send = controlinfo
        #stop sign for approaches
        self.wait = [0,0,0,0,0,0,0,0,0,0,0,0]

    def run(self):
        while True: 
            while self.data.qsize():
                arrival=0
                departure=0
                block=[]
                t=time.time()
                val = self.data.get()
                #0-source, 1-id, 2-timestamp, 3-lane, 4-movement, 5-absolute value of position, 6-length, 7-speed, 8-accelaration, 9-arrival time, 10-departure time
                val[8]=0
                if val[7]==0:
                    arrival = t
                    lastspeed = 8.0
                elif val[5]<=4:
                    arrival = t
                    lastspeed = val[7]
                else:
                    lastspeed = val[7]
                    arrival = val[2] + (val[5]-4)*1.0/val[7]
                

                val[9]=arrival

                if val[4]==1 or val[4]==4 or val[4]==8 or val[4]==11: #straight
                    departure = arrival + (8+val[6])/lastspeed
                elif val[4]==3 or val[4]==5 or val[4]==9 or val[4]==10: #right turn
                    departure = arrival + (math.sqrt(2)*2 +val[6])/lastspeed
                else: #left turn
                    departure = arrival + (math.sqrt(6)*2+val[6])/lastspeed
                val[10]=departure

                if val[4] == 1:
                	block = [6, 7, 8, 10, 11, 12]
                if val[4] == 2:
                	block = [4, 5, 7, 8, 11, 12]
                if val[4] == 3:
            	    block = [6, 8]
                if val[4] == 4:
                	block = [2, 7, 8, 9, 11, 12]
                if val[4] == 5:
                	block = [2, 11]
                if val[4] == 6:
                	block = [1, 3, 7, 8, 11, 12]
                if val[4] == 7:
            	    block = [1,2,4,6,10, 11]
                if val[4] == 8:
                	block = [1,2,3,4,6,12]
                if val[4] == 9:
                	block = [4, 12]
                if val[4] == 10:
                	block = [1, 7]
                if val[4] == 11:
                	block = [1,2,4,5,6,7]
                if val[4] == 12:
                	block = [1,2,4,6,8,9]
                val[11]=block
                self.judge(val)


    def judge(self,val):

#0-source, 1-id, 2-timestamp, 3-lane, 4-movement, 5-absolute value of position, 6-length, 7-speed, 8-accelaration, 9-arrival time, 10-departure time, 11-block
        if self.wait[val[4]-1] < val[9]:
    		#no occupied
            for j in range(len(val[11])-1):
    			#update stop signs
                self.wait[val[11][j]-1] = max(self.wait[val[11][j]-1], val[10])+0.5
        else:
    		#wait
            print("car %s should wait until %s" % (val[1], self.wait[val[4]-1])) 
            val[9]=self.wait[val[4]-1]
            arrival = val[9]
            lastspeed = 8.0
            if val[4]==1 or val[4]==4 or val[4]==8 or val[4]==11: #straight
                departure = arrival + (8+val[5])/lastspeed
            elif val[4]==3 or val[4]==5 or val[4]==9 or val[4]==10: #right turn
                departure = arrival + (math.sqrt(2)*2 +val[6])/lastspeed
            else: #left turn
                departure = arrival + (math.sqrt(6)*2+val[6])/lastspeed
            val[10] = departure
            val[9] = arrival 
            for j in range(len(val[11])-1):
#update stop signs

                self.wait[val[11][j]-1] = max(self.wait[val[11][j]-1], val[10])+0.5
            val[0] = 'stop'
            self.send.put(val)
            print(val)


def main():
    """

    """
    queue = Queue()  
    controlinfo = Queue()
    sender = Sender('Sen.', controlinfo)
    receiver = Receiver('Recv.', queue)  
    cal = Cal('Cal.', queue, controlinfo)  
    sender.start()
    receiver.start()  
    cal.start()  
    sender.join()
    receiver.join()
    cal.join()
    #print('All threads terminate!')



if __name__ == '__main__':
    main()
