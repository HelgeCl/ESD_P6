import numpy as np
import uhd
import time

class SDR:
    def __init__(self, sample_rate, center_freq, rx_gain, tx_gain):
        self.channels = [0, 1]

        self.usrp = uhd.usrp.MultiUSRP()

        self.set_channel_rxtx()
        for chan in self.channels:
            self.usrp.set_rx_rate(sample_rate, chan)
            self.usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)
            self.usrp.set_rx_gain(rx_gain, chan)

            self.usrp.set_tx_rate(sample_rate, chan)
            self.usrp.set_tx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)
            self.usrp.set_tx_gain(tx_gain, chan)

        self.streamer = None
        self.stream_cmd = None
        self.__setup_receiving()

        self.usrp.set_clock_source("internal")
        self.usrp.set_time_source("internal")
        self.usrp.set_time_now(uhd.types.TimeSpec(0.0))
        self.usrp.set_time_unknown_pps(uhd.types.TimeSpec(0.0))
        time.sleep(10)  # Time to lock, and "warmup" time
        print("SDR setup done")

    def set_channel_rx2(self):
        for chan in self.channels:
            self.usrp.set_rx_antenna('RX2', chan)

    def set_channel_rxtx(self):
        for chan in self.channels:
            self.usrp.set_rx_antenna('RX2', chan)

    def __setup_receiving(self):
        st_args = uhd.usrp.StreamArgs("fc32", "sc16")
        st_args.channels = self.channels
        self.streamer = self.usrp.get_rx_stream(st_args)

        self.metadata = uhd.types.RXMetadata()

        self.stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
        self.stream_cmd.stream_now = False
        

    def receive_num(self, num_samples):
        num_samples = int(num_samples)

        num_samples=num_samples+150

        buffer = np.zeros((len(self.channels), num_samples), dtype=np.complex64)
        self.stream_cmd.num_samps = num_samples

        seconds_to_delay = 0.1 #required to sync the two channels
        self.stream_cmd.time_spec = self.usrp.get_time_now() + uhd.types.TimeSpec(seconds_to_delay)
        self.streamer.issue_stream_cmd(self.stream_cmd)
        time.sleep(0.11) #Wait for command to run
        # Pull data
        self.streamer.recv(buffer, self.metadata)

        buffer = buffer[:,150:] #Remove the first 150 samples (corrupted)
        sig_ch1 = buffer[0]
        sig_ch2 = buffer[1]

        return sig_ch1, sig_ch2




