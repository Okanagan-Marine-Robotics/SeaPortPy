import threading
import msgpack
from cobs import cobs
from crc import Calculator, Configuration
import seaport.conf as conf


class SeaPort:
    def __init__(self, serial_port, debug=False):
        """
        Args:
            serial_port: An open serial.Serial object
        """
        self.serial_port = serial_port
        self.lock = threading.Lock()
        self.buffer = bytearray()
        self.callbacks = {}
        self.running = False
        self.thread = None
        self.debug = debug

        self.crc_calculator = Calculator(Configuration(
            width=8,
            polynomial=conf.poly,
            init_value=conf.init_value
        ))

    # === PUBLISHING ===
    def publish(self, channel_id: int, data: dict):
        """
        Send a message with a given channel ID.
        """
        try:
            packed = msgpack.packb(data, use_bin_type=True)
            raw = bytes([channel_id]) + packed
            checksum = self.crc_calculator.checksum(raw)
            message = raw + bytes([checksum])
            framed = cobs.encode(message) + b'\x00'

            with self.lock:
                self.serial_port.write(framed)
                self.serial_port.flush()

        except Exception as e:
            print(f"[SeaPort] Failed to publish message: {e}")

    # === SUBSCRIBING ===
    def subscribe(self, channel_id, callback, debug=False):
        """
        Register a callback for a specific channel ID.
        """
        self.callbacks[channel_id] = (callback, debug)

    def _process_packet(self, packet: bytes, debug=False):
        try:
            decoded = cobs.decode(packet)
            if len(decoded) < 3:
                raise ValueError("Packet too short to contain channel ID and checksum")

            channel_id = decoded[0]
            checksum = decoded[-1]
            payload = decoded[1:-1]

            calculated = self.crc_calculator.checksum(decoded[:-1])
            if calculated != checksum:
                raise ValueError("Checksum mismatch")

            data = msgpack.unpackb(payload, raw=False)
            if debug:
                print(f"[SeaPort DEBUG] Channel: {channel_id}, Data: {data}")
            return channel_id, data

        except Exception as e:
            if debug:
                print(f"[SeaPort DEBUG] Packet error: {e}")
            else:
                print(f"[SeaPort] Failed to process packet: {e}")
            return None, None

    def _run(self):
        while self.running:
            try:
                with self.lock:
                    if self.serial_port.in_waiting:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                    else:
                        continue
                self.buffer.extend(data)

                while self.buffer and 0x00 in self.buffer:
                    idx = self.buffer.index(0x00)
                    if idx == 0:
                        # Remove leading 0x00 to avoid infinite loop
                        self.buffer = self.buffer[1:]
                        continue
                    packet = self.buffer[:idx]
                    self.buffer = self.buffer[idx + 1:]

                    debug_mode = any(cb[1] for cb in self.callbacks.values())
                    channel_id, unpacked = self._process_packet(packet, debug=debug_mode)
                    if channel_id is not None and channel_id in self.callbacks:
                        callback, _ = self.callbacks[channel_id]
                        callback(unpacked)

            except Exception as e:
                print(f"[SeaPort] Error in receiver loop: {e}")
                break

    def start(self):
        """
        Start background reception thread.
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def stop(self):
        """
        Stop background reception thread.
        """
        self.running = False
        if self.thread:
            self.thread.join()
            self.thread = None
