# usage: python arduino_comm.py [port] [drive]
import sys
import time
from enum import IntEnum

import serial

BAUD_RATE = 115200
PORT = "/dev/ttyUSB0"
DRIVE_SPEED = 120

LEFT = 0x00
RIGHT = 0x01


class SentPacketType(IntEnum):
    HANDSHAKE = 0x00
    MOVE_FORWARD = 0x01
    MOVE_BACKWARD = 0x02
    TURN_STATIONARY = 0x03
    STOP = 0x04


class ReceivedPacketType(IntEnum):
    HANDSHAKE_RESPONSE = 0x00
    ACTION_SUCCESS = 0x01
    ACTION_FAILED = 0x02


class ArduinoComm:
    def __init__(self, baud_rate, port):
        self.baud_rate = baud_rate
        self.port = port
        self.arduino = serial.Serial(port=port, baudrate=baud_rate, timeout=1, write_timeout=1)
        self.RECEIVED_PACKET_SIZE = 2

        # //TODO this should make board reset when the port opens
        time.sleep(2)

    def SendPacket(self, messageType, otherData=None):
        if otherData is None:
            otherData = []

        packet = bytearray([messageType])
        i = 0
        while i < len(otherData):
            packet.append(otherData[i])
            i += 1
        self.arduino.write(packet)

    def ReceivePacket(self):
        response = self.arduino.read(self.RECEIVED_PACKET_SIZE)
        if len(response) < self.RECEIVED_PACKET_SIZE:
            return None, None

        return ReceivedPacketType(response[0]), response[1]

    def Forward(self, speed):
        self.SendPacket(SentPacketType.MOVE_FORWARD, [speed])
        return self.ReceivePacket()

    def Backward(self, speed):
        self.SendPacket(SentPacketType.MOVE_BACKWARD, [speed])
        return self.ReceivePacket()

    def Left(self, speed):
        self.SendPacket(SentPacketType.TURN_STATIONARY, [LEFT, speed])
        return self.ReceivePacket()

    def Right(self, speed):
        self.SendPacket(SentPacketType.TURN_STATIONARY, [RIGHT, speed])
        return self.ReceivePacket()

    def Stop(self):
        self.SendPacket(SentPacketType.STOP)
        return self.ReceivePacket()

    def Cleanup(self):
        self.arduino.close()


if __name__ == "__main__":
    port = PORT
    if len(sys.argv) > 1:
        port = sys.argv[1]

    comm = ArduinoComm(BAUD_RATE, port)
    try:
        comm.SendPacket(SentPacketType.HANDSHAKE, [0x67])
        print(comm.ReceivePacket())

        if len(sys.argv) > 2 and sys.argv[2] == "drive":
            moves = [comm.Forward, comm.Backward, comm.Left, comm.Right]
            i = 0
            while i < len(moves):
                print(moves[i](DRIVE_SPEED))
                time.sleep(1)
                comm.Stop()
                i += 1
    finally:
        comm.Stop()
        comm.Cleanup()
