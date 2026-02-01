import openai
from typing import Dict, List, Optional
import json
import re
from .config import settings

openai.api_key = settings.OPENAI_API_KEY


class ScriptAnalyzer:
    """
    Core AI analyzer for YouTube scripts
    Analyzes hook strength, retention, pacing, structure, etc.
    """
    
    ANALYSIS_PROMPT = """You are an expert YouTube script analyst with knowledge of viral video patterns.
Analyze this YouTube script and provide detailed scoring and feedback.

SCRIPT:
{script}

Analyze the following aspects and provide scores (1-10) and detailed feedback:

1. HOOK STRENGTH (First 3-8 seconds)
   - Does it grab attention immediately?
   - Is there a curiosity gap?
   - Score: X/10

2. RETENTION TACTICS
   - Pattern interrupts every 30-60 seconds?
   - Open loops that keep viewers watching?
   - Pacing and momentum?
   - Score: X/10

3. STRUCTURE & FLOW
   - Clear problem → solution arc?
   - Logical progression?
   - Smooth transitions?
   - Score: X/10

4. EMOTIONAL ENGAGEMENT
   - Does it evoke emotion (curiosity, shock, humor)?
   - Personal stories or relatable examples?
   - Score: X/10

5. CALL-TO-ACTION
   - Clear next step?
   - Natural integration?
   - Score: X/10

6. OVERALL VIRALITY POTENTIAL
   - Overall score: X/10
   - Predicted view performance: Low/Medium/High

Return your analysis in this JSON format:
{{
  "overall_score": 8.5,
  "virality_prediction": "High",
  "scores": {{
    "hook": 9,
    "retention": 8,
    "structure": 8,
    "emotional_engagement": 9,
    "cta": 7
  }},
  "strengths": ["Strong hook with immediate question", "Good pacing with pattern interrupts"],
  "weaknesses": ["CTA feels forced", "Missing emotional story in middle section"],
  "improvements": [
    {{
      "section": "Hook",
      "issue": "Could be more specific",
      "suggestion": "Instead of 'Want to grow on YouTube?', try 'This one script mistake cost me 1M views'"
    }},
    {{
      "section": "Retention",
      "issue": "Momentum drops at 2:30 mark",
      "suggestion": "Add a twist or surprising stat here to re-engage viewers"
    }}
  ],
  "viral_patterns_detected": ["Problem-agitate-solution", "Curiosity gap"],
  "viral_patterns_missing": ["Personal transformation story", "Contrarian take"],
  "estimated_retention": "45-55%"
}}

Be specific, actionable, and reference exact parts of the script."""

    @staticmethod
    async def analyze_script(script: str, script_type: str = "general") -> Dict:
        """
        Analyze a YouTube script and return detailed feedback
        
        Args:
            script: The video script text
            script_type: Type of content (tutorial, vlog, review, etc.)
            
        Returns:
            Analysis results with scores and suggestions
        """
        try:
            # Add script type context
            context = f"\nScript Type: {script_type}\n"
            
            response = await openai.ChatCompletion.acreate(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert YouTube script analyst. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": ScriptAnalyzer.ANALYSIS_PROMPT.format(script=script) + context
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Add metadata
            result["word_count"] = len(script.split())
            result["estimated_duration"] = ScriptAnalyzer._estimate_duration(script)
            result["script_length"] = "short" if result["word_count"] < 500 else "medium" if result["word_count"] < 1500 else "long"
            
            return result
            
        except Exception as e:
            print(f"Analysis error: {e}")
            raise Exception(f"Failed to analyze script: {str(e)}")
    
    @staticmethod
    def _estimate_duration(script: str) -> str:
        """Estimate video duration based on word count (150 words/min average)"""
        word_count = len(script.split())
        minutes = word_count / 150
        
        if minutes < 1:
            return f"{int(minutes * 60)} seconds"
        elif minutes < 10:
            return f"{minutes:.1f} minutes"
        else:
            return f"{int(minutes)} minutes"
    
    @staticmethod
    async def compare_scripts(script_a: str, script_b: str) -> Dict:
        """
        A/B test two script versions
        
        Returns which script is likely to perform better
        """
        try:
            response = await openai.ChatCompletion.acreate(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a YouTube script expert. Compare scripts objectively."
                    },
                    {
                        "role": "user",
                        "content": f"""Compare these two YouTube scripts and determine which will perform better:

SCRIPT A:
{script_a}

SCRIPT B:
{script_b}

Return JSON:
{{
  "winner": "A" or "B",
  "confidence": "high/medium/low",
  "reason": "Why this script wins",
  "score_a": 8.5,
  "score_b": 7.2,
  "key_differences": ["Script A has stronger hook", "Script B has better pacing"],
  "recommendation": "Use Script A but incorporate Script B's emotional story"
}}"""
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            raise Exception(f"Failed to compare scripts: {str(e)}")
    
    @staticmethod
    async def generate_improvements(script: str, focus_area: str = "all") -> Dict:
        """
        Generate specific improvements for a script
        
        Args:
            script: Original script
            focus_area: What to improve (hook, retention, structure, all)
        """
        try:
            prompt = f"""Rewrite and improve this YouTube script focusing on: {focus_area}

ORIGINAL SCRIPT:
{script}

Return JSON with:
{{
  "improved_script": "Full improved script here",
  "changes_made": ["Changed hook from X to Y", "Added pattern interrupt at 1:30"],
  "improvement_score": 8.5,
  "explanation": "Why these changes will improve performance"
}}"""
            
            response = await openai.ChatCompletion.acreate(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a YouTube script optimizer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            raise Exception(f"Failed to generate improvements: {str(e)}")


class ViralPatternDetector:
    """Detect viral patterns in scripts"""
    
    VIRAL_PATTERNS = {
        "problem_agitate_solution": r"(?i)(problem|issue|struggle).{50,500}(worse|imagine|what if).{50,500}(solution|answer|fix)",
        "curiosity_gap": r"(?i)(you won't believe|secret|hidden|nobody tells you|shocking)",
        "social_proof": r"(?i)(\d+[kKmM]? (people|viewers|subscribers|users))",
        "transformation": r"(?i)(from .{5,30} to .{5,30}|before .{5,30} after|went from)",
        "contrarian": r"(?i)(stop|don't|never|why you shouldn't|the truth about|myth)",
        "personal_story": r"(?i)(I|my|me).{20,200}(realized|learned|discovered|failed)"
    }
    
    @staticmethod
    def detect_patterns(script: str) -> List[str]:
        """Detect which viral patterns are present"""
        detected = []
        
        for pattern_name, regex in ViralPatternDetector.VIRAL_PATTERNS.items():
            if re.search(regex, script):
                detected.append(pattern_name.replace("_", " ").title())
        
        return detected
