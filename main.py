import cv2
import tkinter as tk  
from tkinter import simpledialog  
import json
from paho.mqtt import client as mqtt_client
import _thread
import time
import random

broker = 'broker.emqx.io'
port = 1883
topic = "msgFfei"
# Generate a Client ID with the publish prefix.
client_id = f'publish-{random.randint(0, 1000)}'
# username = 'emqx'
# password = 'public'
msgtosend={"name":'',"state":''}
pre_frame=None
cap=cv2.VideoCapture("hiv00056.mp4") //change it to your mp4 video

refPt=[]
try:
    with open('config_list.json', 'r') as json_file:  
        MuiltPt = json.load(json_file) 
except FileNotFoundError:
    print("配置文件丢失")
    MuiltPt=[]
except PermissionError:
    print("没有访问权限")
    MuiltPt=[]

with open('init.json', 'r') as json_file:  
    setJson = json.load(json_file) 
cropping=False
stateTxt="RUN"

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client):
    global MuiltPt,msgtosend,stateTxt
    while True:                   
        for s in range(len(MuiltPt)):
            if stateTxt=='RUN': 
                tempSend=MuiltPt[s]
                msgtosend['name']=tempSend[2]
                msgtosend['state']=tempSend[3]            
                result = client.publish(topic, str(msgtosend))
                # result: [0, 1]
                status = result[0]
                if status == 0:
                    print(f"Send `{msgtosend}` to topic `{topic}`")
                else:
                    print(f"Failed to send message to topic {topic}")
                time.sleep(1)
            else:
                result = client.publish(topic, "mechine not running")
                # result: [0, 1]
                status = result[0]
                if status == 0:
                    print(f"mechine not running")
                else:
                    print(f"Failed to send message to topic {topic}")
                time.sleep(1)
def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.loop_stop()
    
def get_input():  
    root = tk.Tk()  
    root.withdraw()  # 隐藏主窗口  
    input_str = simpledialog.askstring("INPUT", "请输入内容：", parent=root)  
    root.destroy()  # 关闭主窗口  
    return input_str

def click_and_crop(event,x,y,flags,param):
    global refPt,cropping,MuiltPt
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt.append((x,y))
        cropping=True
    elif event==cv2.EVENT_LBUTTONUP:
        refPt.append((x,y))
        cropping=False
        tempSqr=(refPt[1][0]-refPt[0][0])*(refPt[1][1]-refPt[0][1])
        if (tempSqr>=200)and(len(refPt)==2):
            refPt.append(len(MuiltPt)+1)    
            refPt.append(0)
            refPt.append(tempSqr)
            MuiltPt.append(refPt)
            with open('config_list.json', 'w') as json_file:  #将更改使用json保存到config_list.json
                json.dump(MuiltPt, json_file)
        refPt=[]

def click_del(event,x,y,flags,param):
    global MuiltPt
    if event == cv2.EVENT_LBUTTONDOWN:
        tempK=-1
        for k in range (len(MuiltPt)):
            print(MuiltPt[k])
            tempDPt=MuiltPt[k]
            xPt=tempDPt[0]
            yPt=tempDPt[1]
            if (xPt[0]<=x and yPt[0]>=x) and (xPt[1]<=y and yPt[1]>=y):
                tempK=k
                break
        if tempK!=-1:
            del MuiltPt[tempK]  
            with open('config_list.json', 'w') as json_file:  #将更改使用json保存到config_list.json
                json.dump(MuiltPt, json_file)  

def click_rename(event,x,y,flags,param):
    global MuiltPt
    if event == cv2.EVENT_LBUTTONDOWN:
        tempR=-1
        for r in range (len(MuiltPt)):
            print(MuiltPt[r])
            tempRPt=MuiltPt[r]
            xPt=tempRPt[0]
            yPt=tempRPt[1]
            if (xPt[0]<=x and yPt[0]>=x) and (xPt[1]<=y and yPt[1]>=y):
                tempR=r
                break
        if tempR!=-1:
            user_input = get_input()
            if user_input != None:
                tempchange=MuiltPt[tempR]
                tempchange[2]=user_input
                MuiltPt[tempR]=tempchange
                with open('config_list.json', 'w') as json_file:  #将更改使用json保存到config_list.json
                    json.dump(MuiltPt, json_file)  

if __name__ == '__main__':
    _thread.start_new_thread ( run )

    if not cap.isOpened():
        print("can't open ...")

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            gray_img = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            gray_img = cv2.GaussianBlur(gray_img,(5,5),0)
            # cv2.imshow('gray',gray_img)
            if pre_frame is None:
                pre_frame=gray_img
            else:
                img_delta=cv2.absdiff(pre_frame,gray_img)
                thresh=cv2.threshold(img_delta,25,255,cv2.THRESH_BINARY)[1]
                # cv2.imshow('diff',thresh)
                if len(MuiltPt):
                    for a in range(len(MuiltPt)): 
                        tempPt=MuiltPt[a]
                        APt=tempPt[0]
                        BPt=tempPt[1]
                        sumPt=(BPt[0]-APt[0])*(BPt[1]-APt[1])
                        if sumPt!=0:
                            sumPtPix=0
                            for i in range (BPt[0]-APt[0]):
                                for j in range  (BPt[1]-APt[1]):
                                    sumPtPix=sumPtPix+thresh[(APt[1]+j),(APt[0]+i)] #数据访问时x，y对调
                                    thresh[(APt[1]+j),(APt[0]+i)]=255
                            MVConfi=sumPtPix/sumPt
                            # print(MVConfi)
                            if MVConfi>setJson['sensitivity']: #灵敏度参数
                                B=0
                                G=255
                                R=0
                                MuiltPt[a][3]=0
                            else:
                                B=0
                                G=0
                                R=255
                                if MuiltPt[a][3]<=500:
                                    MuiltPt[a][3]+=1
                            cv2.rectangle(frame,tempPt[0],tempPt[1],(B,G,R),2)
                            cv2.putText(frame,str(tempPt[2]),((APt[0]),(APt[1]-5)),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0, 255,255), 2)
                if stateTxt == 'EDIT':
                    cv2.putText(frame, stateTxt, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255,255), 2) 
                else:
                    cv2.putText(frame, stateTxt, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255,0), 2) 
                cv2.imshow('diff',thresh)
                cv2.imshow('Video', frame)

            pre_frame=gray_img    
            # 按下'q'键退出循环
            pressedKey = cv2.waitKey(1) & 0xFF
            if pressedKey == ord('q'):
                break
            elif pressedKey == ord('e'):
                stateTxt='EDIT'
                cv2.setMouseCallback("Video",click_and_crop)
            elif pressedKey == ord('r'):
                stateTxt='RUN'
                cv2.setMouseCallback("Video",lambda *args : None)
            elif pressedKey == ord('n'):
                stateTxt='RENAME'
                cv2.setMouseCallback("Video",click_rename)
            elif pressedKey == ord('d'):
                stateTxt='DELETE'
                cv2.setMouseCallback("Video",click_del)           
        else:
            break

    cap.release()

    cv2.destroyAllWindows()
