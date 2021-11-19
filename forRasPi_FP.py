
from digi.xbee.devices import XBeeDevice
from digi.xbee.models.status import NetworkDiscoverStatus
import im_wireless as imw
import threading
from time import sleep

PORT = "/dev/ttyUSB0"

BAUD_RATE = 115200

device = XBeeDevice(PORT,BAUD_RATE)

SLAVE_ADR = 0x30

iwc = imw.IMWireClass(SLAVE_ADR)

SM = 1
# 1のときsleep,0のとき通常動作

def recIM920():
    global SM
    while True:
        rx_data = iwc.Read_920()                        # 受信処理           
        if len(rx_data) >= 11:                          # 11は受信データのノード番号+RSSI等の長さ
            if (rx_data[2]==',' and    
                rx_data[7]==',' and rx_data[10]==':'):
                rx_xbeestate = rx_data[11:12]
                print(rx_xbeestate)
                if(rx_xbeestate == '1'):
                    SM = 1
                elif(rx_xbeestate == '2'):
                    SM = 0
                    # ここよくわかんないけど，なんとなく書き換えました


def sendIM(mesC):
    if mesC[4:] == 'mdt':
        iwc.Write_920('txdu0001,'+mesC[1:4])
        print(mesC[1:4])
    else:
        pass

def sleepBC():
    DATA_TO_SEND = 'sleep'
    while True:
        try:
            device.send_data_broadcast(DATA_TO_SEND)
            print("sleep")
            sleep(5)
        except:
            pass
        
        finally:
            if SM == 0:
                print("sleep finish")
                break

def main():
    
    print(" +---------------------+")
    print(" | IM920sL and XBee R4 |")
    print(" +---------------------+\n")

    iwc.Write_920('ECIO')

    try:
        device.open()

        xbee_network = device.get_network()
        xbee_network.set_discovery_timeout(15)
        xbee_network.clear()

        def callback_device_discovered(remote):
                print("Device discovered: %s" % remote)

        def callback_discovery_finished(status):
            if status == NetworkDiscoveryStatus.SUCCESS:
                print("探すのおわり")
            else:
                print("There was an error discovering devices: %s" % status.description)

        xbee_network.add_device_discovered_callback(callback_device_discovered)
        xbee_network.add_discovery_process_finished_callback(callback_discovery_finished)
        xbee_network.start_discovery_process()
        print("Discovering remote XBee devices...")
        print("Waiting for data...\n")

        while True:
            try:
                if SM == 1:
                    sleepBC()
                elif SM == 0:
                    xbee_message = device.read_data()
                    if xbee_message is not None:

                        xbee_network = device.get_network()

                        print("From %s >> %s" % (xbee_message.remote_device.node_id(),
                                                 xbee_message.data.decode()))
                        addr = xbee_message.remote_device.node_id()
                        mes = xbee_message.data.decode()

                        sendIM(mes)
            except:
                pass

    finally:
        iwc.gpio_clean()
        if device is not None and device.is_open():
            device.close()

if __name__ == '__main__':
    thread1 = threading.Thread(target = recIM920)
    thread1.start()
    main()
