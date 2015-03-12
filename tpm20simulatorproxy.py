""" Simple Script to handle the "TSS.MSR v1.1 TPM2 Simulator" from
    Microsoft(tm) Research and connect it to David Howells tpm_user_emul
    kernel driver.
    Latest version of the TSS.MSR TPM2 Simulator can be found at
    https://tpm2lib.codeplex.com/

    Latest version of tpm_user_emul can be found at
    https://github.com/PeterHuewe/linux-tpmdd/tree/tpm-emulator

    SPDX-License-Identifier: BSD-2-Clause

     Copyright (c) 2014, Peter Huewe
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are 
met:

    1) Redistributions of source code must retain the above copyright notice,
    this list of conditions and the following disclaimer.

    2) Redistributions in binary form must reproduce the above copyright 
notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS 
IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
    THE POSSIBILITY OF SUCH DAMAGE.

"""
import socket
import binascii

class TPM2Simulator():
    """ Simple class to handle the "TSS.MSR v1.1 TPM2 Simulator" from
        Microsoft(tm) Research and connect it to David Howells tpm_user_emul
        kernel driver.
        The command bytes have been observed by analyzing the traffic between
        the simulator and a valid client. The exact meaning of the bytes are
        not known to me. No reverse engineering was done.
    """

    def __init__(self):
        """ Initializes the connection to the simulator and initializes the
            simulator device by sending some control commands """

        self.ctrl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ctrl.connect(("localhost", 2322))
        self.data = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data.connect(("localhost", 2321))

        self.data.sendall(bytes([0, 0, 0, 0x0f]))
        self.data.sendall(bytes([0, 0, 0, 0x01]))
        print(self.data.recv(4))
        print(self.data.recv(4))
        print(self.data.recv(4))
        self.ctrl.sendall(bytes([0, 0, 0, 0x02]))
        print(self.ctrl.recv(4))
        self.ctrl.sendall(bytes([0, 0, 0, 0x0c]))
        print(self.ctrl.recv(4))
        self.ctrl.sendall(bytes([0, 0, 0, 0x01]))
        print(self.ctrl.recv(4))
        self.ctrl.sendall(bytes([0, 0, 0, 0x0b]))
        print(self.ctrl.recv(4))
        startup_clear=bytes ([0x80, 0x01, 0x00, 0x00, 0x00, 0x0C, 0x00, 0x00, 0x01, 0x44, 0x00, 0x00])
        self.transmit_command(startup_clear)

    def transmit_command(self, msg):
        """ transmits a tpm20 command to the simulator by prepending the
            necessary command bytes and length and stripping the additional
            status code of the simulator from the response"""

        cmd = binascii.unhexlify("0000000800000000")
        cmd += len(msg).to_bytes(1, "big")
        cmd += msg
        print("Cmd {}".format(binascii.hexlify(cmd)))
        self.data.sendall(cmd)
        tpm_resp_len = 0
        while tpm_resp_len == 0:
            tpm_resp_len = int.from_bytes(self.data.recv(4), "big")

        tpm_resp = b""
        while len(tpm_resp) != tpm_resp_len+4:
            tpm_resp += self.data.recv(tpm_resp_len+4-len(tpm_resp))
        print(tpm_resp_len)
        print("Resp {}".format(binascii.hexlify(tpm_resp)))
        return tpm_resp[:-4]

    def run_simulator_proxy(self):
        """ Connects the proxy to /dev/tpm_emul and handles the read/write
            requests from the kernel"""
        with open("/dev/tpm_emul", "w+b", buffering=0) as tpm_emul:
            while True:
                stream = tpm_emul.read(4096)
                print("IN {}".format(binascii.hexlify(stream)))
                resp = self.transmit_command(stream)
                tpm_emul.write(resp)


if __name__ == "__main__":
    tpm2 = TPM2Simulator()
    tpm2.run_simulator_proxy()
