#pip install XBeeDevice

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

bldnumber = '001'      #各建物ごとに変える
state = 1

def sendIM(mesC):
    if mesC[4:] == 'mdt':
        iwc.Write_920('txdu0001,'+mesC[:4])
        print(mesC[:4])
    else:
        pass

def recIM920():
    global state
    while True:
        rx_data = iwc.Read_920()
        if len(rx_data) >= 11:                          # 11は受信データのノード番号+RSSI等の長さ
            if (rx_data[2]==',' and    
                rx_data[7]==',' and rx_data[10]==':'):
                rx_data = rx_data[11:15]
                print(rx_data)

                if rx_data == bldnumber +'0' or rx_data == '0000':
                    state = 0
                    print('OK')
                elif rx_data == bldnumber +'1' or rx_data == '0001':
                    state = 1
                    print('NG')
                else:
                    pass

def main():
    global state
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
                xbee_message = device.read_data()
                if xbee_message is not None:

                    xbee_network = device.get_network()

                    print("From %s >> %s" % (xbee_message.remote_device.get_64bit_addr(),
                                             xbee_message.data.decode()))
                    addr = xbee_message.remote_device.get_64bit_addr()
                    mes = xbee_message.data.decode()

                    if state == 0:
                        sendIM(mes)
                    else:
                        pass
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
