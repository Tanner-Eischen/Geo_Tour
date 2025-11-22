"""
INTEGRATION GUIDE: Adding Cinematic Enhancement to Your Pipeline

This shows the THREE ways to integrate the cinematic enhancer:

Option 1: RECOMMENDED - Automatic enhancement in scene_planner.py
Option 2: Explicit enhancement in main pipeline
Option 3: Optional enhancement with toggle
"""

# ============================================================
# OPTION 1: AUTOMATIC ENHANCEMENT IN SCENE_PLANNER.PY
# ============================================================
# This is the cleanest approach - scene planner automatically
# produces cinematic descriptions

"""
Modify scene_planner.py by adding these imports at the top:
"""

# ADD THIS IMPORT
from cinematic_enhancer import CinematicEnhancer

"""
Then modify the ScenePlanner class:
"""

class ScenePlanner:
    def __init__(self, api_key=None, use_cinematic_enhancement=True):
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.client = OpenAI(api_key=self.api_key)

        # ADD THIS
        self.use_cinematic_enhancement = use_cinematic_enhancement
        self.cinematic_enhancer = CinematicEnhancer() if use_cinematic_enhancement else None

    def create_plan(self, script_data, target_scenes=None, scene_duration=None):
        """Create a scene-by-scene plan from script"""
        safe_print("🎬 Creating scene plan...")

        # ... existing code for generating scene_plan ...

        # ADD THIS BLOCK BEFORE RETURNING
        # Enhance visual descriptions with cinematic vocabulary
        if self.use_cinematic_enhancement and self.cinematic_enhancer:
            safe_print("🎥 Enhancing scenes with cinematic prompting...")
            scene_plan = self.cinematic_enhancer.enhance_scene_plan(
                scene_plan, 
                original_user_prompt=script_data.get('title', '')
            )
            safe_print("✅ Cinematic enhancement applied")

        return scene_plan


# ============================================================
# OPTION 2: EXPLICIT ENHANCEMENT IN MAIN PIPELINE
# ============================================================
# Enhance after scene planning, before storyboard generation

"""
In your main pipeline (wherever you call these modules):
"""

from script_generator import ScriptGenerator
from scene_planner import ScenePlanner
from storyboard_generator import StoryboardGenerator
from video_generator import VideoGenerator
from cinematic_enhancer import CinematicEnhancer  # ADD THIS

def generate_video_pipeline(user_prompt):
    # Step 1: Generate script
    script_gen = ScriptGenerator()
    script = script_gen.generate(user_prompt)

    # Step 2: Create scene plan
    scene_planner = ScenePlanner()
    scene_plan = scene_planner.create_plan(script)

    # Step 3: ENHANCE WITH CINEMATICS (ADD THIS)
    enhancer = CinematicEnhancer()
    scene_plan = enhancer.enhance_scene_plan(scene_plan, user_prompt)
    print("✅ Applied cinematic enhancement to all scenes")

    # Step 4: Generate storyboard images
    storyboard_gen = StoryboardGenerator()
    images = storyboard_gen.generate(scene_plan)

    # Step 5: Generate video clips
    video_gen = VideoGenerator()
    clips = video_gen.generate_clips(scene_plan, storyboard_images=images)

    return clips


# ============================================================
# OPTION 3: OPTIONAL ENHANCEMENT WITH USER TOGGLE
# ============================================================
# Let users choose whether to use cinematic enhancement

def generate_video_pipeline_with_option(user_prompt, use_cinematic=True, 
                                       cinematic_intensity="high"):
    """
    Args:
        use_cinematic: Enable/disable cinematic enhancement
        cinematic_intensity: "low", "medium", "high" (future feature)
    """
    script_gen = ScriptGenerator()
    script = script_gen.generate(user_prompt)

    scene_planner = ScenePlanner()
    scene_plan = scene_planner.create_plan(script)

    # Optional cinematic enhancement
    if use_cinematic:
        print(f"🎥 Applying cinematic enhancement (intensity: {cinematic_intensity})...")
        enhancer = CinematicEnhancer()
        scene_plan = enhancer.enhance_scene_plan(scene_plan, user_prompt)
        print("✅ Cinematic prompting applied")
    else:
        print("ℹ️  Using standard visual descriptions")

    storyboard_gen = StoryboardGenerator()
    images = storyboard_gen.generate(scene_plan)

    video_gen = VideoGenerator()
    clips = video_gen.generate_clips(scene_plan, storyboard_images=images)

    return clips


# ============================================================
# EXAMPLE: BEFORE AND AFTER COMPARISON
# ============================================================

def show_before_after_example():
    """Demonstrate the enhancement effect"""

    # Simulate scene plan from your pipeline
    basic_scene_plan = {
        "scenes": [
            {
                "scene_number": 1,
                "narration": "Mars surface shows evidence of ancient water",
                "visual_description": "Red rocky Martian landscape with dried river channels",
                "duration": 6
            },
            {
                "scene_number": 2,
                "narration": "Olympus Mons towers over the horizon",
                "visual_description": "Massive volcanic mountain on Mars",
                "duration": 6
            },
            {
                "scene_number": 3,
                "narration": "Ice caps glisten at the poles",
                "visual_description": "White ice covering Mars polar region",
                "duration": 6
            }
        ]
    }

    print("\n" + "="*60)
    print("BEFORE: Basic Visual Descriptions")
    print("="*60)
    for scene in basic_scene_plan["scenes"]:
        print(f"\nScene {scene['scene_number']}:")
        print(f"  {scene['visual_description']}")

    # Apply cinematic enhancement
    enhancer = CinematicEnhancer()
    enhanced_plan = enhancer.enhance_scene_plan(
        basic_scene_plan, 
        "Documentary about Mars geology"
    )

    print("\n" + "="*60)
    print("AFTER: Cinematic Enhanced Descriptions")
    print("="*60)
    for scene in enhanced_plan["scenes"]:
        print(f"\nScene {scene['scene_number']}:")
        print(f"  {scene['visual_description']}")

    print("\n" + "="*60)
    print("KEY DIFFERENCES:")
    print("="*60)
    print("✅ Professional camera framing (wide shots, close-ups, etc.)")
    print("✅ Lighting conditions specified (golden hour, volumetric, etc.)")
    print("✅ Depth and scale cues for layered composition")
    print("✅ Movement implications for I2V models")
    print("✅ Subject-specific enhancements (geological scale, etc.)")
    print("✅ Atmospheric and quality keywords (IMAX, cinematic)")


if __name__ == "__main__":
    show_before_after_example()
