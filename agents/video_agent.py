from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
)


class VideoAgent:
    def generate(self, topic: str, audio_path: str, output_path: str):
        audio = AudioFileClip(audio_path)

        duration = audio.duration

        background = ColorClip(
            size=(1280, 720),
            color=(20, 20, 20),
            duration=duration,
        )

        title = TextClip(
            topic,
            fontsize=50,
            color="white",
            size=(1000, None),
            method="caption",
        ).set_position("center").set_duration(duration)

        final = CompositeVideoClip([background, title])
        final = final.set_audio(audio)

        final.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
        )

        return output_path