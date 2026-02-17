import os
import mpv
from pynput.keyboard import Key, Listener
import time
import vlc
import pygame
from gpiozero import Button, LED
from signal import pause

led = LED(16)
led.on()



print("Press the button to see a message. Press Ctrl+C to exit.")

# Pause the script to wait for events
pause()

# # Initialize MPV player
# device= "bcm2835 Headphones"
# player = mpv.MPV(ytdl=False, input_default_bindings=True, audio_device=device, input_vo_keyboard=True)
# speed = 1.0
# duration_seconds = 1  # Duration to play the audio in seconds

# # The MP3 file you want to play
# audio_file_path = 'heartbeat.mp3' # Update with your file's actual path
# filename = audio_file_path

# sleep_seconds = 0.1
# rate = 0.1
# pygame.mixer.init()

# # Start playing the music
# # loops=0 plays it once (default), start=0.0 starts from the beginning
# while True:



#     # Load the music file
#     pygame.mixer.music.load(filename)
#     pygame.mixer.music.play(loops=0, start=0.0)

#     print(f"Playing '{filename}' for {duration_seconds} seconds...")

#     # Keep the program running for the specified duration using sleep
#     time.sleep(duration_seconds)

#     # Stop the music after the duration
#     pygame.mixer.music.stop()
#     print("Playback stopped.")
#     sleep_seconds += rate
#     time.sleep(sleep_seconds)
#     if sleep_seconds > 1.5:
#         rate = -0.1
#     elif sleep_seconds < 0.1:
#         rate = 0.1

# # Optional: Quit the mixer and pygame

# pygame.mixer.quit()
# pygame.quit()














# print(f"Playing audio: {audio_file_path}")
# print("Press 'g' to increase speed, 'f' to decrease speed. Press 'Esc' to exit.")

# # Start playing the audio file
# ret = player.play(audio_file_path)
# while True:
#     pass
# instance = vlc.Instance()

# # Create a Media Player object
# player = instance.media_player_new()

# # Create a Media object from the file path
# media = instance.media_new(audio_file_path)

# # Set the media to the player
# player.set_media(media)

# # Start playback
# player.play()

# # Wait for the media to start playing
# time.sleep(1)

# # Initial playback rate
# rate = 1.0

# try:
#     while True:
#         # Increase the rate by 10% (multiply by 1.1)
#         rate *= 1.1
        
#         # Set the new playback rate
#         # The set_rate method returns 0 on success, -1 on error
#         if player.set_rate(rate) == -1:
#             print(f"Error: Could not set rate to {rate:.2f}x. The maximum speed might be reached or exceeded.")
#             # You might choose to break the loop or cap the speed here
#             break
            
#         print(f"Current playback speed: {rate:.2f}x")
        
#         # Wait for 1 second before increasing the speed again
#         time.sleep(2)
        
#         # Check if the player is still playing
#         # is_playing() returns 0 if stopped, 1 if playing/paused
#         if player.is_playing() == 0:
#             # If the media has ended, reset rate and restart for a continuous loop
#             player.set_media(media) # Re-set media to ensure loop
#             player.play()
#             rate = 1.0 # Reset rate for the new loop iteration
#             time.sleep(1) # Wait for it to start again
            
# except KeyboardInterrupt:
#     # Stop the player when interrupted by the user (e.g., Ctrl+C)
#     player.stop()
#     print("Playback stopped.")