import pyaudio
import wave
import numpy as np
import time
import socket
import threading
import argparse
import glob

CHUNK = 1024
MUSIC_CONST = 0.25
TIMEOUT = 0.01
TIME_TO_DRINK = 45
PORT = 49393
DRUMS_IP = '172.20.10.10'
BASS_IP = '172.20.10.11'
VOCALS_IP = '172.20.10.12'

# Flag for thread to exit
stop_thread = False

# volume start values
bass_times = []
vocals_times = []
drums_times = []

liquids = {DRUMS_IP: 0, BASS_IP: 0, VOCALS_IP: 0}
message_to_ip = {'d': DRUMS_IP, 'b': BASS_IP, 'v': VOCALS_IP}
# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def np_convert(data):
    return np.frombuffer(data.readframes(CHUNK), dtype=np.int16)


def filter_according_to_drink():
    total_times = len(bass_times) + len(vocals_times) + len(drums_times) + 1
    return (music_data * MUSIC_CONST + bass_data * (len(bass_times) / total_times) +
            vocals_data * (len(vocals_times) / total_times) + drums_data * (len(drums_times) / total_times)).astype(
        np.int16)


def send_receive(ip, port, timeout=TIMEOUT):
    # Define the message to send in the UDP packet
    message = b'get_info'
    # Send the UDP packet to the target IP address and port number
    sock.sendto(message, (ip, port))
    # Set a timeout for the recvfrom() call
    sock.settimeout(timeout)
    try:
        # Receive the response from the UDP packet
        response = sock.recvfrom(CHUNK)[0].decode('utf-8').split(' ')
        # return the volume factor based on the response
        return int(response[0]), response[1].strip()
    except socket.timeout:
        # If the recvfrom() call times out, return None
        return


def send_receive_all(ips, port):
    global liquids, stop_thread
    # Continuously listen for messages from the UDP socket
    while not stop_thread:
        for ip in ips:
            pair = send_receive(ip, port)
            if pair is None:
                continue
            val, sent_to = pair
            liquids[message_to_ip[sent_to]] = val


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--playlist")
    args = parser.parse_args()

    playlist_2d_lst = []
    with open(args.playlist, "r") as playlist:
        for line in playlist.readlines():
            if line[0] != '#':
                playlist_2d_lst.append(glob.glob(line.strip("\n")))

    # Start the UDP socket thread
    udp_thread = threading.Thread(target=send_receive_all, args=([BASS_IP, DRUMS_IP, VOCALS_IP], PORT))
    udp_thread.start()

    for song in playlist_2d_lst:
        # Open the audio files (bass, drums, music, vocals)
        bass = wave.open(song[0], "rb")
        drums = wave.open(song[1], "rb")
        music = wave.open(song[2], "rb")
        vocals = wave.open(song[3], "rb")

        # Initialize Pyaudio
        p = pyaudio.PyAudio()

        # Open a stream
        music_stream = p.open(format=p.get_format_from_width(bass.getsampwidth()),
                              channels=bass.getnchannels(),
                              rate=bass.getframerate(),
                              output=True)

        # Start playing the audio files
        music_data = np_convert(music)
        bass_data = np_convert(bass)
        vocals_data = np_convert(vocals)
        drums_data = np_convert(drums)

        start_time = time.time()

        while len(bass_data) or len(vocals_data) or len(drums_data) or len(music_data):
            print(len(drums_times), len(bass_times), len(vocals_times))

            newdata = filter_according_to_drink()

            # Play the mixed audio data
            music_stream.write(newdata.tobytes())

            current_time = time.time()

            if liquids[BASS_IP]:
                bass_times.append(current_time)
            if liquids[DRUMS_IP]:
                drums_times.append(current_time)
            if liquids[VOCALS_IP]:
                vocals_times.append(current_time)

            bass_times = [t for t in bass_times if current_time - t < TIME_TO_DRINK]
            drums_times = [t for t in drums_times if current_time - t < TIME_TO_DRINK]
            vocals_times = [t for t in vocals_times if current_time - t < TIME_TO_DRINK]

            # Read the next chunk of audio data
            music_data = np_convert(music)
            bass_data = np_convert(bass)
            vocals_data = np_convert(vocals)
            drums_data = np_convert(drums)

        # Close the audio files, streams and stop the thread
        music.close()
        bass.close()
        vocals.close()
        drums.close()
        music_stream.close()
        p.terminate()

    # Stop the UDP socket thread    
    stop_thread = True
    udp_thread.join()
