"""
Acoustic Speaker Diarization Engine.
Extracts spectral centroid, pitch/timbre energy, zero-crossing rates, and sub-band Mel energy
directly from audio waveforms to cluster speakers (Teacher vs Student, Multi-Speaker Discussions, Solo).
"""

from __future__ import annotations

import logging
import math
import os
import re
import struct
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.schemas.audio import DiarizationSummary, DiarizedSegmentItem

logger = logging.getLogger(__name__)

# Linguistic question/interrupt cues for classroom dynamics
STUDENT_SPEECH_PATTERNS = [
    r"\b(excuse me|sorry to interrupt|professor|dr\.|can you repeat|could you explain|i have a question)\b",
    r"\b(what happens if|why does|is that because|does that mean|how do we know)\b",
    r"\b(could you go back|what is the difference|is this on the exam)\b",
    r"\?$",
]


class DiarizationEngine:
    """
    Acoustic & Linguistic Speaker Diarization Engine.
    Combines waveform spectral feature clustering with conversational heuristics.
    """

    def diarize_segments(
        self,
        raw_segments: List[Dict[str, Any]],
        audio_path: Optional[Path] = None,
        diarization_mode: str = "lecture",
        primary_speaker_label: str = "Teacher",
        secondary_speaker_label: str = "Student",
    ) -> Tuple[List[DiarizedSegmentItem], DiarizationSummary]:
        """
        Diarizes transcribed segments using acoustic waveform feature clustering
        and conversational turn heuristics.
        """
        if not raw_segments:
            return [], DiarizationSummary()

        mode = (diarization_mode or "lecture").lower()

        # 1. Extract acoustic voice features from audio if available
        features = None
        if audio_path and audio_path.exists():
            try:
                features = self._extract_acoustic_features(audio_path, raw_segments)
            except Exception as exc:
                logger.warning("Acoustic feature extraction failed, falling back to heuristic: %s", exc)

        # 2. Cluster segments based on mode
        if mode in {"discussion", "conversation"}:
            return self._diarize_discussion_acoustic(raw_segments, features)
        elif mode == "solo":
            return self._diarize_solo(raw_segments, primary_speaker_label)
        else:
            return self._diarize_lecture_acoustic(
                raw_segments, features, primary_speaker_label, secondary_speaker_label
            )

    def _extract_acoustic_features(
        self,
        audio_path: Path,
        segments: List[Dict[str, Any]],
    ) -> Optional[np.ndarray]:
        """
        Extracts acoustic feature vectors (RMS, ZCR, Spectral Centroid, Spread, Subband Energy)
        for each timestamped segment.
        """
        try:
            with wave.open(str(audio_path), "rb") as wf:
                channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                nframes = wf.getnframes()
                raw_bytes = wf.readframes(nframes)

            if sampwidth == 2:
                samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            elif sampwidth == 1:
                samples = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
            else:
                samples = np.frombuffer(raw_bytes, dtype=np.float32)

            if channels > 1:
                samples = samples.reshape(-1, channels).mean(axis=1)

            feature_rows = []
            for seg in segments:
                start_sec = float(seg.get("start", 0.0))
                end_sec = float(seg.get("end", start_sec + 1.0))

                start_idx = max(0, int(start_sec * framerate))
                end_idx = min(len(samples), int(end_sec * framerate))

                seg_samples = samples[start_idx:end_idx]
                if len(seg_samples) < 512:
                    # Pad short slices
                    seg_samples = np.pad(seg_samples, (0, max(0, 512 - len(seg_samples))))

                # Feature 1: RMS Energy
                rms = float(np.sqrt(np.mean(seg_samples**2) + 1e-9))

                # Feature 2: Zero Crossing Rate (ZCR)
                zcr = float(np.mean(np.abs(np.diff(np.sign(seg_samples + 1e-9)))) / 2.0)

                # Feature 3 & 4: Spectral Centroid & Spread via FFT
                fft_mag = np.abs(np.fft.rfft(seg_samples))
                freqs = np.fft.rfftfreq(len(seg_samples), d=1.0 / framerate)

                sum_mag = np.sum(fft_mag) + 1e-9
                centroid = float(np.sum(freqs * fft_mag) / sum_mag)
                spread = float(np.sqrt(np.sum(((freqs - centroid) ** 2) * fft_mag) / sum_mag))

                # Feature 5: Subband energy ratios (Voice fundamental 80-300Hz, Mid 300-1500Hz, High 1500-4000Hz)
                b1 = float(np.sum(fft_mag[(freqs >= 80) & (freqs < 300)]) / sum_mag)
                b2 = float(np.sum(fft_mag[(freqs >= 300) & (freqs < 1500)]) / sum_mag)
                b3 = float(np.sum(fft_mag[(freqs >= 1500) & (freqs < 4000)]) / sum_mag)

                feature_rows.append([rms, zcr, centroid / 4000.0, spread / 2000.0, b1, b2, b3])

            return np.array(feature_rows, dtype=np.float32)
        except Exception as err:
            logger.debug("Failed to compute acoustic features: %s", err)
            return None

    def _diarize_lecture_acoustic(
        self,
        raw_segments: List[Dict[str, Any]],
        features: Optional[np.ndarray],
        primary_label: str,
        secondary_label: str,
    ) -> Tuple[List[DiarizedSegmentItem], DiarizationSummary]:
        """
        Combines acoustic clustering with classroom conversational structure.
        """
        num_segs = len(raw_segments)
        cluster_labels = np.zeros(num_segs, dtype=int)

        # Apply acoustic clustering if we have multi-segment audio
        if features is not None and len(features) >= 4:
            try:
                from sklearn.cluster import KMeans

                # Standardize feature matrix
                mean = np.mean(features, axis=0)
                std = np.std(features, axis=0) + 1e-6
                norm_feat = (features - mean) / std

                # Check if there is acoustic separation (variance across centroids/ZCR)
                variance = np.var(norm_feat, axis=0).sum()

                # If variance is very low, single speaker is speaking
                if variance > 1.8:
                    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
                    labels = kmeans.fit_predict(norm_feat)

                    # Determine which cluster is the primary teacher (the one with higher total duration)
                    durations_0 = sum(
                        float(raw_segments[i].get("end", 0)) - float(raw_segments[i].get("start", 0))
                        for i in range(num_segs)
                        if labels[i] == 0
                    )
                    durations_1 = sum(
                        float(raw_segments[i].get("end", 0)) - float(raw_segments[i].get("start", 0))
                        for i in range(num_segs)
                        if labels[i] == 1
                    )

                    # Cluster with dominant speech time is Teacher
                    teacher_cluster = 0 if durations_0 >= durations_1 else 1
                    cluster_labels = (labels != teacher_cluster).astype(int)
            except Exception as e:
                logger.debug("Acoustic clustering fallback: %s", e)

        diarized_items: List[DiarizedSegmentItem] = []
        teacher_time = 0.0
        student_time = 0.0
        teacher_count = 0
        student_count = 0
        total_words = 0

        for i, seg in enumerate(raw_segments):
            text = seg.get("text", "").strip()
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start + 1.0))
            duration = max(0.1, end - start)
            words = len(text.split())
            total_words += words

            # Acoustic cluster decision
            is_acoustic_student = bool(cluster_labels[i] == 1)

            # Linguistic cues (question or interrupt)
            is_linguistic_student = any(re.search(pat, text, re.IGNORECASE) for pat in STUDENT_SPEECH_PATTERNS)

            # Explicit speaker override if provided
            existing = seg.get("speaker")
            if existing:
                speaker = primary_label if "teach" in existing.lower() or "facult" in existing.lower() else secondary_label
            elif is_linguistic_student and duration < 12.0:
                speaker = secondary_label
            elif is_acoustic_student and duration < 15.0 and is_linguistic_student:
                speaker = secondary_label
            else:
                speaker = primary_label

            if speaker == primary_label:
                teacher_time += duration
                teacher_count += 1
            else:
                student_time += duration
                student_count += 1

            diarized_items.append(
                DiarizedSegmentItem(
                    speaker=speaker,
                    start_time=round(start, 2),
                    end_time=round(end, 2),
                    text=text,
                    confidence=float(seg.get("confidence", 0.94)),
                    word_count=words,
                )
            )

        total_time = teacher_time + student_time
        talk_ratio = round(teacher_time / total_time, 2) if total_time > 0 else 1.0

        summary = DiarizationSummary(
            total_segments=len(diarized_items),
            teacher_segments=teacher_count,
            student_segments=student_count,
            teacher_speaking_time_sec=round(teacher_time, 2),
            student_speaking_time_sec=round(student_time, 2),
            teacher_talk_ratio=talk_ratio,
            total_words=total_words,
        )

        return diarized_items, summary

    def _diarize_discussion_acoustic(
        self,
        raw_segments: List[Dict[str, Any]],
        features: Optional[np.ndarray],
    ) -> Tuple[List[DiarizedSegmentItem], DiarizationSummary]:
        """
        Multi-speaker conversation diarization using acoustic clustering (K-Means)
        and pause boundary detection.
        """
        num_segs = len(raw_segments)
        k = min(3, max(2, int(math.ceil(num_segs / 4.0))))
        labels = np.zeros(num_segs, dtype=int)

        if features is not None and len(features) >= k:
            try:
                from sklearn.cluster import KMeans

                mean = np.mean(features, axis=0)
                std = np.std(features, axis=0) + 1e-6
                norm_feat = (features - mean) / std

                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(norm_feat)
            except Exception:
                labels = np.array([i % k for i in range(num_segs)])
        else:
            labels = np.array([i % k for i in range(num_segs)])

        diarized_items: List[DiarizedSegmentItem] = []
        speaker_times: Dict[str, float] = {}
        total_words = 0

        for i, seg in enumerate(raw_segments):
            text = seg.get("text", "").strip()
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start + 1.0))
            duration = max(0.1, end - start)
            words = len(text.split())
            total_words += words

            speaker_name = f"Speaker {labels[i] + 1}"
            speaker_times[speaker_name] = speaker_times.get(speaker_name, 0.0) + duration

            diarized_items.append(
                DiarizedSegmentItem(
                    speaker=speaker_name,
                    start_time=round(start, 2),
                    end_time=round(end, 2),
                    text=text,
                    confidence=float(seg.get("confidence", 0.94)),
                    word_count=words,
                )
            )

        speaker_1_time = speaker_times.get("Speaker 1", 0.0)
        total_time = sum(speaker_times.values())
        talk_ratio = round(speaker_1_time / total_time, 2) if total_time > 0 else 0.5

        summary = DiarizationSummary(
            total_segments=len(diarized_items),
            teacher_segments=sum(1 for s in diarized_items if s.speaker == "Speaker 1"),
            student_segments=sum(1 for s in diarized_items if s.speaker != "Speaker 1"),
            teacher_speaking_time_sec=round(speaker_1_time, 2),
            student_speaking_time_sec=round(total_time - speaker_1_time, 2),
            teacher_talk_ratio=talk_ratio,
            total_words=total_words,
        )

        return diarized_items, summary

    def _diarize_solo(
        self,
        raw_segments: List[Dict[str, Any]],
        speaker_label: str = "Presenter",
    ) -> Tuple[List[DiarizedSegmentItem], DiarizationSummary]:
        """Uniform single speaker diarization for solo lectures or talks."""
        diarized_items: List[DiarizedSegmentItem] = []
        total_time = 0.0
        total_words = 0

        for seg in raw_segments:
            text = seg.get("text", "").strip()
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start + 1.0))
            duration = max(0.1, end - start)
            words = len(text.split())
            total_words += words
            total_time += duration

            diarized_items.append(
                DiarizedSegmentItem(
                    speaker=speaker_label,
                    start_time=round(start, 2),
                    end_time=round(end, 2),
                    text=text,
                    confidence=float(seg.get("confidence", 0.95)),
                    word_count=words,
                )
            )

        summary = DiarizationSummary(
            total_segments=len(diarized_items),
            teacher_segments=len(diarized_items),
            student_segments=0,
            teacher_speaking_time_sec=round(total_time, 2),
            student_speaking_time_sec=0.0,
            teacher_talk_ratio=1.0,
            total_words=total_words,
        )

        return diarized_items, summary
