#test
from digi.xbee.devices import XBeeDevice
from digi.xbee.models.status import NetworkDiscoveryStatus
import im_wireless as imw
import threading
from time import sleep

PORT = "/dev/ttyUSB0"

BAUD_RATE = 115200

device = XBeeDevice(PORT,BAUD_RATE)

SLAVE_ADR = 0x30

iwc = imw.IMWireClass(SLAVE_ADR)

#global SM  #1のときsleep,0のとき通常動作,2のときsleep解除動作
SM = 1

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
                    SM = 2


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
            sleep(10)
            
        except:
            print('except')
            pass
        
        finally:
            if SM == 2:
                print("sleep stop")
                break
        
def wakeupBC():
        global SM
        senL = ['S101']

        DATA_TO_SEND = 'wakeUp'
        print('wakeUp')
        while len(senL) != 0:
                device.send_data_broadcast(DATA_TO_SEND)

                xbee_message = device.read_data()
                addr = xbee_message.remote_device.get_64bit_addr()
                mes = xbee_message.data.decode()
                if mes[-6:] == 'wakeUp':
                    try:
                        senL.remove(mes[:4])
                        SM = 0
                        print(SM)
                        print("wakeup stop")
                        break
                        
                    except ValueError:
                        pass

def main():
    
    print(" +---------------------+")
    print(" | IM920sL and XBee R3 |")
    print(" +---------------------+\n")

    iwc.Write_920('ECIO')

    try:
        device.open()

        device.flush_queues()
        
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
                    print("sleep start")
                    sleepBC()
                elif SM == 2:
                    print("wakeup start")
                    wakeupBC()
                elif SM == 0:
                    xbee_message = device.read_data()
                    if xbee_message is not None:

                        xbee_network = device.get_network()

                        print("From %s >> %s" % (xbee_message.remote_device.get_64bit_addr(),
                                                 xbee_message.data.decode()))
                        addr = xbee_message.remote_device.get_64bit_addr()
                        mes = xbee_message.data.decode()

                        remote_device = xbee_network.discover_device(mes[:4])
                        if remote_device is None:
                            print("Could not find the remote device")
                            
                        else:
                            device.send_data(remote_device,mes)
                            print("Success")

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
