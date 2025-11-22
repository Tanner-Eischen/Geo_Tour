"""
Main pipeline orchestrator - coordinates all modules
"""
import json
from pathlib import Path
from datetime import datetime

from config import ensure_directories, OUTPUT_DIR, USE_STORYBOARD
from script_generator import ScriptGenerator
from scene_planner import ScenePlanner
from storyboard_generator import StoryboardGenerator
from video_generator import VideoGenerator
from audio_generator import AudioGenerator
from video_assembler import VideoAssembler


def safe_print(*args, **kwargs):
    """Safely print messages, handling closed file errors in Streamlit"""
    try:
        print(*args, **kwargs)
    except (IOError, OSError, ValueError):
        # Silently fail if stdout is closed (Streamlit context)
        pass


class VideoPipeline:
    def __init__(self, 
                 openai_api_key=None,
                 video_api_key=None,
                 tts_api_key=None,
                 video_provider="replicate",
                 tts_provider="elevenlabs",
                 use_storyboard=None,
                 svd_model=None,
                 sdxl_model=None):
        """
        Initialize the video generation pipeline
        
        Args:
            openai_api_key (str): API key for OpenAI (GPT-4)
            video_api_key (str): API key for video generation (Replicate API key)
            tts_api_key (str): API key for text-to-speech
            video_provider (str): Video generation provider (replicate, runwayml, pika, etc.)
            tts_provider (str): TTS provider (elevenlabs, openai, etc.)
            use_storyboard (bool): Whether to generate storyboard images first (default: from config)
        """
        ensure_directories()
        
        self.script_gen = ScriptGenerator(openai_api_key)
        self.scene_planner = ScenePlanner(openai_api_key)
        self.storyboard_gen = StoryboardGenerator(video_api_key)
        self.video_gen = VideoGenerator(video_api_key, svd_model=svd_model, sdxl_model=sdxl_model)
        self.audio_gen = AudioGenerator(tts_api_key, tts_provider)
        self.assembler = VideoAssembler()
        
        self.use_storyboard = use_storyboard if use_storyboard is not None else USE_STORYBOARD
        self.current_project = None
    
    def run(self, user_prompt, output_filename=None, num_scenes=None, scene_duration=None, progress_callback=None):
        """
        Run the complete pipeline
        
        Args:
            user_prompt (str): User's description of desired video
            output_filename (str): Optional custom output filename
            num_scenes (int): Number of scenes to generate
            scene_duration (int): Duration per scene in seconds
            progress_callback (callable): Optional callback for progress updates
            
        Returns:
            dict: Results including paths and metadata
        """
        safe_print("\n" + "=" * 70)
        safe_print("🎬 VIDEO GENERATION PIPELINE")
        safe_print("=" * 70)
        safe_print(f"Prompt: {user_prompt}")
        safe_print("=" * 70 + "\n")
        
        # Create project data structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_project = {
            "prompt": user_prompt,
            "timestamp": timestamp,
            "steps": {}
        }
        
        try:
            # Step 1: Generate script
            if progress_callback:
                progress_callback(1, 6, "📝 Generating script...", "Creating narrative structure")
            safe_print("\n[1/6] Script Generation")
            safe_print("-" * 70)
            script_data = self.script_gen.generate(user_prompt)
            self.current_project["steps"]["script"] = script_data
            if progress_callback:
                progress_callback(1, 6, "✅ Script generated", f"Title: {script_data.get('title', 'Untitled')}")
            
            # Step 2: Plan scenes
            if progress_callback:
                progress_callback(2, 6, "🎬 Planning scenes...", f"Creating {num_scenes or 5} scenes")
            safe_print("\n[2/6] Scene Planning")
            safe_print("-" * 70)
            scene_plan = self.scene_planner.create_plan(script_data, target_scenes=num_scenes, scene_duration=scene_duration)
            self.current_project["steps"]["scenes"] = scene_plan
            if progress_callback:
                progress_callback(2, 6, "✅ Scenes planned", f"{len(scene_plan.get('scenes', []))} scenes created")
            
            # Step 3: Generate storyboard (optional)
            storyboard_images = None
            if self.use_storyboard:
                if progress_callback:
                    progress_callback(3, 6, "🎨 Generating storyboards...", "Creating visual storyboards for each scene")
                safe_print("\n[3/6] Storyboard Generation")
                safe_print("-" * 70)
                storyboard_images = self.storyboard_gen.generate(scene_plan)
                self.current_project["steps"]["storyboard"] = storyboard_images
                if progress_callback:
                    progress_callback(3, 6, "✅ Storyboards generated", f"{len(storyboard_images or [])} storyboard images created")
            else:
                if progress_callback:
                    progress_callback(3, 6, "⏭️ Storyboard generation skipped", "Using text-to-video generation")
                safe_print("\n[3/6] Storyboard Generation (skipped)")
                safe_print("-" * 70)
            
            # Step 4: Generate video clips
            if progress_callback:
                progress_callback(4, 6, "🎥 Generating video clips...", "Creating animated video clips for each scene")
            safe_print("\n[4/6] Video Clip Generation")
            safe_print("-" * 70)
            clip_paths = self.video_gen.generate_clips(scene_plan, storyboard_images=storyboard_images)
            self.current_project["steps"]["clips"] = clip_paths
            if progress_callback:
                progress_callback(4, 6, "✅ Video clips generated", f"{len(clip_paths)} video clips created")
            
            # Step 5: Generate voiceover
            if progress_callback:
                progress_callback(5, 6, "🎙️ Generating voiceover...", "Creating audio narration from script")
            safe_print("\n[5/6] Voiceover Generation")
            safe_print("-" * 70)
            audio_path = self.audio_gen.generate(script_data)
            self.current_project["steps"]["audio"] = audio_path
            if progress_callback:
                progress_callback(5, 6, "✅ Voiceover generated", f"Audio file created: {Path(audio_path).name}")
            
            # Step 6: Assemble final video
            if progress_callback:
                progress_callback(6, 6, "🎬 Assembling final video...", "Combining video clips with audio")
            safe_print("\n[6/6] Final Assembly")
            safe_print("-" * 70)
            
            if not output_filename:
                safe_title = "".join(c for c in script_data['title'] if c.isalnum() or c in (' ', '-', '_'))
                safe_title = safe_title.replace(' ', '_')[:50]
                output_filename = f"{safe_title}_{timestamp}.mp4"
            
            output_path = OUTPUT_DIR / output_filename
            final_video = self.assembler.assemble(clip_paths, audio_path, output_path)
            self.current_project["steps"]["final_video"] = final_video
            if progress_callback:
                progress_callback(6, 6, "✅ Video complete!", f"Final video saved: {output_filename}")
            
            # Save project metadata
            self._save_metadata()
            
            # print summary
            self._print_summary(final_video)
            
            return {
                "success": True,
                "video_path": final_video,
                "script": script_data,
                "scenes": scene_plan,
                "project_data": self.current_project
            }
            
        except Exception as e:
            safe_print(f"\n❌ Pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "project_data": self.current_project
            }
    
    def _save_metadata(self):
        """Save project metadata to JSON file"""
        metadata_path = OUTPUT_DIR / f"project_{self.current_project['timestamp']}.json"
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_project, indent=2, fp=f, ensure_ascii=False)
        
        safe_print(f"\n💾 Metadata saved: {metadata_path.name}")
    
    def _print_summary(self, video_path):
        """print pipeline completion summary"""
        safe_print("\n" + "=" * 70)
        safe_print("✨ PIPELINE COMPLETE!")
        safe_print("=" * 70)
        safe_print(f"Title: {self.current_project['steps']['script']['title']}")
        safe_print(f"Scenes: {len(self.current_project['steps']['scenes']['scenes'])}")
        safe_print(f"Output: {video_path}")
        safe_print("=" * 70 + "\n")


if __name__ == "__main__":
    # Example usage
    pipeline = VideoPipeline(
        openai_api_key="your-key-here",  # Will use env var if not provided
        video_provider="replicate",
        tts_provider="elevenlabs"
    )
    
    result = pipeline.run("Explain how photosynthesis works in simple terms")
    
    if result["success"]:
        safe_print(f"✅ Video created: {result['video_path']}")
    else:
        safe_print(f"❌ Failed: {result['error']}")
