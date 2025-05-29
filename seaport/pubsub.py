import msgpack
import seaport.conf
from cobs import cobs
from crc import Calculator, Configuration


class Subscriber:
    def __init__(self, data_generator):
        self.data_generator = data_generator
        self.buffer = bytearray()
        self.callbacks = {}  # channel_id -> callback function

        # Set up CRC calculator (CRC-8 SMBus)
        self.crc_calculator = Calculator(Configuration(
            width=8,
            polynomial=conf.poly,
            init_value=conf.init_value
        ))

    def subscribe(self, channel_id, callback):
        """Register a callback for a specific channel ID."""
        self.callbacks[channel_id] = callback

    def _process_packet(self, packet: bytes):
        """Decode, validate, and unpack a single COBS-framed packet."""
        print(packet.hex())
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
            return channel_id, data

        except Exception as e:
            print(f"Failed to process packet: {e}")
            return None, None

    def feed(self):
        """Continuously read from the data source and dispatch messages to callbacks."""
        try:
            while True:
                data = next(self.data_generator)
                if not data:
                    continue

                self.buffer.extend(data)

                while 0x00 in self.buffer:
                    idx = self.buffer.index(0x00)
                    if idx == 0:
                        self.buffer = self.buffer[1:]
                        continue
                    packet = self.buffer[:idx]
                    self.buffer = self.buffer[idx + 1:]

                    channel_id, unpacked = self._process_packet(packet)
                    if channel_id is not None and channel_id in self.callbacks:
                        self.callbacks[channel_id](unpacked)
        except StopIteration:
            print("Data source ended.")
        except Exception as e:
            print(f"Error in Subscriber run loop: {e}")

class Publisher:
    def __init__(self, output_stream):
        """
        Args:
            output_stream: A writeable stream (e.g., serial.Serial)
        """
        self.output_stream = output_stream
        self.crc_calculator = Calculator(Configuration(
            width=8,
            polynomial=conf.poly,
            init_value=conf.init_value
        ))

    def publish(self, channel_id: int, data: dict):
        """
        Publishes a message to the output stream.

        Args:
            channel_id: Identifier for the message type.
            data: A dict or any msgpack-serializable object.
        """
        try:
            # Serialize the payload using msgpack
            packed = msgpack.packb(data, use_bin_type=True)

            # Prepend channel ID and calculate checksum
            raw = bytes([channel_id]) + packed
            checksum = self.crc_calculator.checksum(raw)
            message = raw + bytes([checksum])

            # COBS encode and append frame delimiter
            framed = cobs.encode(message) + b'\x00'

            # Send
            self.output_stream.write(framed)
            self.output_stream.flush()

        except Exception as e:
            print(f"Failed to publish message: {e}")