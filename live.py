import random
import subprocess
import time
from multiprocessing import Process
from ftplib import FTP
import socket

YOUTUBE_URL = 'rtmp://a.rtmp.youtube.com/live2'
KEYS = ['398j-pxdw-28cy-bcm4-apvb', 'pxa5-44q5-tpw6-8x4v-ffpa', 'p859-ffgb-g1u8-qbad-13h6', 'key4', 'key5', 'key6', 'key7', 'key8', 'key9', 'key10']

FTP_HOSTS = ['mp4hub.me', 'mp4hub.me', 'mp4hub.me', 'host4', 'host5', 'host6', 'host7', 'host8', 'host9', 'host10']
FTP_USERNAMES = ['admin_host', 'admin_host', 'admin_host', 'user4', 'user5', 'user6', 'user7', 'user8', 'user9', 'user10']
FTP_PASSWORDS = ['Sjha@2005', 'Sjha@2005', 'Sjha@2005', 'pass4', 'pass5', 'pass6', 'pass7', 'pass8', 'pass9', 'pass10']
REMOTE_AUDIO_FOLDERS = ['live', 'di', 'live2', 'live4', 'dar', 'pra', 'audio7/', 'audio8/', 'audio9/', 'audio10/']
REMOTE_AUDIO_FOLDER = ['/live', '/di', '/live2', '/live4', '/dar', '/pra', 'audio7/', 'audio8/', 'audio9/', 'audio10/']

MP4_FILES = ['/home/container/live.mp4', '/home/container/di.mp4', '/home/container/livve2.mp4', '/home/container/live4.mp4', '/home/container/dar.mp4', '/home/container/pra.mp4', '/path/to/live7.mp4', '/path/to/live8.mp4', '/path/to/live9.mp4', '/path/to/live10.mp4']

def validate_hostname(hostname):
  try:
    socket.gethostbyname(hostname)
    return True
  except socket.gaierror:
    return False

def connect_to_ftp(hostname, username, password):
  retries = 0
  while retries < 3:
    try:
      ftp = FTP(hostname)
      ftp.login(user=username, passwd=password)
      return ftp
    except Exception as e:
      print(f"Error connecting to FTP server {hostname}: {e}")
      retries += 1
      time.sleep(5)
  return None

def retrieve_audio_files(ftp, remote_folder):
  audio_files = []
  try:
    ftp.cwd(remote_folder)
    audio_files = [f for f in ftp.nlst() if f.endswith('.mp3')]
  except Exception as e:
    print(f"Error retrieving audio files: {e}")
    print(audio_files)
  return audio_files

def generate_ffmpeg_command(audio_file, mp4_file, output_url):
  return [
  'ffmpeg',
  '-loglevel', 'info', '-y', '-re', # -re for loop
  '-stream_loop', '-1', '-i', mp4_file,
  #'-f', 'lavfi', '-i', f"movie=filename={mp4_file}:loop=0,setpts=N/({FRAME_RATE}*TB)",
  '-i', audio_file,
  '-c:v', 'libx264', '-preset', 'ultrafast', '-b:v', '200k', '-maxrate', '200k', '-bufsize', '400k',
  '-framerate', '15', '-video_size', '640x360', '-vf', 'format=yuv420p', '-g', '30', '-shortest', '-strict', 'experimental',
  '-c:a', 'copy', # Assuming the audio is already encoded properly in the MP3
  '-map', '0:v', '-map', '1:a', # Map video and audio streams
  '-f', 'flv', output_url
 ]

def stream_audio(i, output_url):
  ftp = connect_to_ftp(FTP_HOSTS[i], FTP_USERNAMES[i], FTP_PASSWORDS[i])
  if not ftp:
    print(f"Failed to connect to FTP server for index {i}.")
    return

  audio_files = retrieve_audio_files(ftp, REMOTE_AUDIO_FOLDERS[i])
  print(audio_files)
  ftp.quit()
   
  if not audio_files:
    print(f"No audio files found on FTP server for index {i}.")
    return

  for audio_file in audio_files:
    audio_file_path = f"ftp://{FTP_USERNAMES[i]}:{FTP_PASSWORDS[i]}@{FTP_HOSTS[i]}{REMOTE_AUDIO_FOLDER[i]}/{audio_file}"
    mp4_file = MP4_FILES[i]
    ffmpeg_command = generate_ffmpeg_command(audio_file_path, mp4_file, output_url)
    print(f"Streaming audio file: {audio_file}")
    subprocess.call(ffmpeg_command)

def stream_process(i, youtube_url, keys):
  while True:
    output_url = f"{youtube_url}/{keys[i]}"
    stream_audio(i, output_url)

    try:
      time.sleep(10) # Increased sleep time to reduce CPU usage
    except KeyboardInterrupt:
      print("Keyboard interrupt received. Ending streaming process.")
      break

def main():
  for hostname in FTP_HOSTS[:]:
    if not validate_hostname(hostname):
      print(f"Hostname {hostname} is not resolvable. Skipping.")
      FTP_HOSTS.remove(hostname)

  processes = []
  for i in range(len(FTP_HOSTS)):
    p = Process(target=stream_process, args=(i, YOUTUBE_URL, KEYS))
    p.daemon = True # Set the process as a daemon
    p.start()
    processes.append(p)

  try:
    while True:
      time.sleep(1) # Keep the main program running
  except KeyboardInterrupt:
    print("Keyboard interrupt received. Ending streaming processes.")
    for p in processes:
      p.terminate() # Terminate each child process
    for p in processes:
      p.join() # Join each child process

if __name__ == "__main__":
  main() 
