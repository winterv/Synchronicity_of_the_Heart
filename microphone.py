import time
import numpy as np
import pyaudio
import sys
import config


def find_loopback_device():
    """Find a WASAPI loopback device on Windows, or return None if not found/not Windows"""
    p = pyaudio.PyAudio()
    loopback_device = None
    
    try:
        # Get WASAPI host API index
        wasapi_index = None
        for i in range(p.get_host_api_count()):
            api_info = p.get_host_api_info_by_index(i)
            if 'WASAPI' in str(api_info.get('name', '')).upper():
                wasapi_index = i
                break
        
        if wasapi_index is None:
            print('WASAPI not available. Loopback mode may not work properly.')
            return None
        
        # Strategy 1: Look for devices with "Loopback" or "Stereo Mix" in the name
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            device_name = str(device_info.get('name', '')).lower()

            if ('stereo mix' in device_name):
                loopback_device = i
                print('Found loopback device: {} (index {})'.format(device_info.get('name'), i))
                return loopback_device
        
        # Strategy 2: Find WASAPI input devices that correspond to output devices
        # WASAPI loopback devices often have the same name as their corresponding output device
        output_devices = {}
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if (int(device_info.get('maxOutputChannels', 0)) > 0 and 
                device_info.get('hostApi', 0) == wasapi_index):
                device_name = device_info.get('name', '')
                output_devices[device_name] = i
        
        # Now look for input devices with matching names (these are likely loopback)
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            device_name = device_info.get('name', '')
            if (int(device_info.get('maxInputChannels', 0)) > 0 and 
                device_info.get('hostApi', 0) == wasapi_index and
                device_name in output_devices):
                loopback_device = i
                print('Found WASAPI loopback device: {} (index {})'.format(device_name, i))
                break
        
    except Exception as e:
        print('Error finding loopback device: {}'.format(e))
    finally:
        p.terminate()
    
    return loopback_device


def list_audio_devices():
    """List all available audio devices for debugging"""
    p = pyaudio.PyAudio()
    print('\nAvailable audio devices:')
    print('=' * 80)
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        print('Index {}: {}'.format(i, device_info.get('name')))
        print('  Host API: {}'.format(p.get_host_api_info_by_index(int(device_info.get('hostApi', 0))).get('name')))
        print('  Max Input Channels: {}'.format(device_info.get('maxInputChannels', 0)))
        print('  Max Output Channels: {}'.format(device_info.get('maxOutputChannels', 0)))
        print('  Default Sample Rate: {}'.format(device_info.get('defaultSampleRate', 0)))
        print()
    p.terminate()


def start_stream(callback):
    p = pyaudio.PyAudio()
    frames_per_buffer = int(config.MIC_RATE / config.FPS)
    
    # Determine input device and parameters
    input_device_index = None
    if config.USE_LOOPBACK:
        if sys.platform == 'win32':
            # Try to find a WASAPI loopback device
            input_device_index = find_loopback_device()
            if input_device_index is None:
                print('Warning: Loopback mode enabled but no loopback device found.')
                print('Listing available devices for debugging:')
                list_audio_devices()
                print('Falling back to default input device.')
                print('On Windows, you may need to enable "Stereo Mix" in Sound settings.')
        else:
            print('Loopback mode is enabled, but automatic detection is primarily for Windows.')
            print('On Linux/Mac, you may need to configure a virtual audio device.')
            print('Listing available devices:')
            list_audio_devices()
    
    # Open the audio stream
    stream_kwargs = {
        'format': pyaudio.paInt16,
        'channels': 1,
        'rate': config.MIC_RATE,
        'input': True,
        'frames_per_buffer': frames_per_buffer,
    }
    
    if input_device_index is not None:
        stream_kwargs['input_device_index'] = input_device_index
    
    stream = p.open(**stream_kwargs)
    
    if config.USE_LOOPBACK:
        print('Using loopback mode - capturing audio output')
    else:
        print('Using microphone input mode')
    
    overflows = 0
    prev_ovf_time = time.time()
    while True:
        try:
            y = np.frombuffer(stream.read(frames_per_buffer, exception_on_overflow=False), dtype=np.int16)
            y = y.astype(np.float32)
            stream.read(stream.get_read_available(), exception_on_overflow=False)
            callback(y)
        except IOError:
            overflows += 1
            if time.time() > prev_ovf_time + 1:
                prev_ovf_time = time.time()
                print('Audio buffer has overflowed {} times'.format(overflows))
    stream.stop_stream()
    stream.close()
    p.terminate()
