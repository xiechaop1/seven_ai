import base64

def calculate_pcm_duration(
        buffer: bytes, 
        sample_rate: int = 16000, 
        channels: int = 1, 
        sample_format: str = "S16LE") -> float:
    sample_format_bytes = {
        "S16LE": 2,   
        "S32LE": 4,   
        "F32LE": 4   
    }
    
    if sample_format not in sample_format_bytes:
        raise ValueError(f"Unsupported sample format: {sample_format}")
    
    bytes_per_sample = sample_format_bytes[sample_format]
    
    bytes_per_frame = channels * bytes_per_sample
    
    total_frames = len(buffer) // bytes_per_frame
    
    duration_seconds = total_frames / sample_rate
    
    return duration_seconds

def audio_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        buffer = f.read()
    return base64.b64encode(buffer).decode()