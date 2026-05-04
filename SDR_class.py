import numpy as np
import uhd
import time


class SDR:
    def __init__(self, sample_rate, center_freq, rx_gain, tx_gain, chan_rx, chan_tx):
        self.chan_rx = chan_rx  # [0, 1]
        self.chan_tx = chan_tx

        self.usrp = uhd.usrp.MultiUSRP()

        self.set_channel_rxtx()
        for chan in self.chan_rx:
            self.usrp.set_rx_rate(sample_rate, chan)
            self.usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)
            self.usrp.set_rx_gain(rx_gain, chan)

        for chan in self.chan_tx:
            self.usrp.set_tx_rate(sample_rate, chan)
            self.usrp.set_tx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)
            self.usrp.set_tx_gain(tx_gain, chan)

        self.rx_streamer = None
        self.rx_stream_cmd = None
        self.rx_cont_stream_cmd = None
        self.rx_metadata = None

        self.tx_streamer = None
        self.tx_stream_cmd = None
        self.tx_metadata = None

        self.usrp.set_clock_source("internal")
        self.usrp.set_time_source("internal")
        self.usrp.set_time_now(uhd.types.TimeSpec(0.0))
        self.usrp.set_time_unknown_pps(uhd.types.TimeSpec(0.0))
        #time.sleep(10)  # Time to lock, and "warmup" time H123 Temp
        print("SDR setup done")

    def set_channel_rx2(self):
        channels = list(set(self.chan_rx + self.chan_tx))
        for chan in channels:
            self.usrp.set_rx_antenna('RX2', chan)

    def set_channel_rxtx(self):
        channels = list(set(self.chan_rx + self.chan_tx))
        for chan in channels:
            self.usrp.set_rx_antenna('TX/RX', chan)

    def setup_receiving(self):
        st_args = uhd.usrp.StreamArgs("fc32", "sc16")
        st_args.channels = self.chan_rx
        self.rx_streamer = self.usrp.get_rx_stream(st_args)

        self.rx_metadata = uhd.types.RXMetadata()

        self.rx_stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
        self.rx_stream_cmd.stream_now = False

        self.rx_cont_stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        self.rx_cont_stream_cmd.stream_now = True

    def receive_num(self, num_samples):
        num_samples = int(num_samples)

        num_samples = num_samples+150

        buffer = np.zeros((len(self.chan_rx), num_samples), dtype=np.complex64)
        self.rx_stream_cmd.num_samps = num_samples

        seconds_to_delay = 0.1  # required to sync the two channels
        self.rx_stream_cmd.time_spec = self.usrp.get_time_now() + uhd.types.TimeSpec(seconds_to_delay)
        self.rx_streamer.issue_stream_cmd(self.rx_stream_cmd)
        time.sleep(0.11)  # Wait for command to run
        # Pull data
        self.rx_streamer.recv(buffer, self.rx_metadata)

        buffer = buffer[:, 150:]  # Remove the first 150 samples (corrupted)
        sig_ch1 = buffer[0]
        sig_ch2 = buffer[1]

        return sig_ch1, sig_ch2

    def start_receive_cont(self):
        self.rx_streamer.issue_stream_cmd(self.rx_cont_stream_cmd)

    def stop_receive_cont(self):
        stop_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
        self.rx_streamer.issue_stream_cmd(stop_cmd)

    def receive_cont_samples(self, buffer):
        """Example buffer:
                self.cont_buffer = np.zeros(10000, dtype=np.complex64)

        """
        self.rx_streamer.recv(buffer, self.rx_metadata)

    def setup_transmit(self):
        st_args = uhd.usrp.StreamArgs("fc32", "sc16")
        st_args.channels = self.self.chan_tx
        self.tx_streamer = self.usrp.get_tx_stream(st_args)


        # Continuous loop transmission
        self.tx_metadata = uhd.types.TXMetadata()
        self.tx_metadata.start_of_burst = True
        self.tx_metadata.end_of_burst = True

    def transmit(self, samples):
        self.tx_streamer.send(samples, self.tx_metadata)
