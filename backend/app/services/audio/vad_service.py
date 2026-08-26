"""
Voice Activity Detection (VAD) & Audio Enhancement Service.
Detects active speech regions, filters classroom noise, and isolates speech segments.
"""

from __future__ import annotations

import logging
import math
import struct
import wave
from pathlib import Path
from typing import List, Optional, Tuple

from app.schemas.audio import VADSegmentItem

logger = logging.getLogger(__name__)


class VADService:
    """Detects active speech intervals and filters dead air/silence from classroom audio."""

    def __init__(
        self,
        frame_duration_ms: int = 30,
        energy_threshold: float = 0.02,
        min_speech_duration_sec: float = 0.3,
        max_silence_gap_sec: float = 0.6,
    ):
        self.frame_duration_ms = frame_duration_ms
        self.energy_threshold = energy_threshold
        self.min_speech_duration_sec = min_speech_duration_sec
        self.max_silence_gap_sec = max_silence_gap_sec

    def detect_speech_intervals(self, audio_path: Path) -> List[VADSegmentItem]:
        """
        Processes a 16kHz mono WAV file and returns active speech intervals with timestamps.
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            with wave.open(str(audio_path), "rb") as wf:
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                num_frames = wf.getnframes()
                raw_bytes = wf.readframes(num_frames)

            if num_frames == 0 or sample_rate == 0:
                return []

            total_duration = num_frames / float(sample_rate)

            # Unpack 16-bit PCM samples
            fmt = f"<{num_frames * channels}h"
            try:
                samples = struct.unpack(fmt, raw_bytes)
            except Exception:
                # If mono/stereo mismatch, unpack by chunk
                samples = []
                bytes_per_sample = sample_width * channels
                for i in range(0, len(raw_bytes), bytes_per_sample):
                    chunk = raw_bytes[i : i + 2]
                    if len(chunk) == 2:
                        samples.append(struct.unpack("<h", chunk)[0])

            frame_size = int(sample_rate * (self.frame_duration_ms / 1000.0))
            if frame_size <= 0:
                frame_size = 480  # 30ms at 16kHz

            # Compute normalized RMS energy per frame
            frame_energies: List[Tuple[float, float, bool]] = []
            max_possible_amp = 32768.0

            for i in range(0, len(samples), frame_size):
                frame = samples[i : i + frame_size]
                if not frame:
                    continue
                start_ts = i / float(sample_rate)
                end_ts = min(total_duration, (i + len(frame)) / float(sample_rate))

                # RMS energy
                sum_sq = sum(s * s for s in frame)
                rms = math.sqrt(sum_sq / len(frame)) / max_possible_amp
                is_speech = rms >= self.energy_threshold
                frame_energies.append((start_ts, end_ts, is_speech))

            # Merge consecutive speech frames
            raw_intervals: List[Tuple[float, float]] = []
            in_speech = False
            current_start = 0.0
            last_end = 0.0

            for start_ts, end_ts, is_speech in frame_energies:
                if is_speech:
                    if not in_speech:
                        in_speech = True
                        current_start = start_ts
                    last_end = end_ts
                else:
                    if in_speech:
                        in_speech = False
                        raw_intervals.append((current_start, last_end))

            if in_speech:
                raw_intervals.append((current_start, last_end))

            # Bridge small silence gaps between speech bursts
            merged_intervals: List[Tuple[float, float]] = []
            for start, end in raw_intervals:
                if not merged_intervals:
                    merged_intervals.append((start, end))
                else:
                    prev_start, prev_end = merged_intervals[-1]
                    gap = start - prev_end
                    if gap <= self.max_silence_gap_sec:
                        merged_intervals[-1] = (prev_start, end)
                    else:
                        merged_intervals.append((start, end))

            # Filter out very short noise bursts
            results: List[VADSegmentItem] = []
            for start, end in merged_intervals:
                duration = end - start
                if duration >= self.min_speech_duration_sec:
                    results.append(
                        VADSegmentItem(
                            start_sec=round(start, 2),
                            end_sec=round(end, 2),
                            duration_sec=round(duration, 2),
                            energy_score=1.0,
                        )
                    )

            # If audio has no distinct high-energy pauses, treat entire audio as single segment
            if not results and total_duration > 0.5:
                results.append(
                    VADSegmentItem(
                        start_sec=0.0,
                        end_sec=round(total_duration, 2),
                        duration_sec=round(total_duration, 2),
                        energy_score=1.0,
                    )
                )

            logger.info("VAD detected %d speech segments in %s (total: %.2fs)", len(results), audio_path.name, total_duration)
            return results

        except Exception as exc:
            logger.warning("VAD processing error on %s: %s; falling back to full audio window", audio_path, exc)
            return [VADSegmentItem(start_sec=0.0, end_sec=60.0, duration_sec=60.0, energy_score=1.0)]
