from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List
from ...core.security import get_current_user, check_rate_limit, require_plan
from ...core.analyzer import ScriptAnalyzer, ViralPatternDetector
from ...schemas.schemas import (
    AnalyzeScriptRequest,
    AnalysisResponse,
    ScriptCompareRequest,
    ComparisonResponse,
    ImproveScriptRequest,
    ImprovementResponse,
    AnalysisHistory,
    AnalysisListItem,
    UserStats
)
from ...models.models import User, Analysis, Comparison
from ...api.deps import get_db

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_script(
    request: AnalyzeScriptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a YouTube script
    """
    # Check rate limit
    if not check_rate_limit(current_user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly limit reached. Upgrade to Pro for more analyses."
        )
    
    try:
        # Run AI analysis
        result = await ScriptAnalyzer.analyze_script(
            script=request.script,
            script_type=request.script_type
        )
        
        # Detect viral patterns
        detected_patterns = ViralPatternDetector.detect_patterns(request.script)
        result["viral_patterns_detected"] = detected_patterns
        
        # Save to database
        analysis = Analysis(
            user_id=current_user.id,
            script_text=request.script,
            script_type=request.script_type,
            title=request.title,
            overall_score=result["overall_score"],
            virality_prediction=result["virality_prediction"],
            scores=result["scores"],
            strengths=result["strengths"],
            weaknesses=result["weaknesses"],
            improvements=result["improvements"],
            viral_patterns_detected=result.get("viral_patterns_detected", []),
            viral_patterns_missing=result.get("viral_patterns_missing", []),
            word_count=result["word_count"],
            estimated_duration=result["estimated_duration"],
            estimated_retention=result.get("estimated_retention")
        )
        
        db.add(analysis)
        
        # Update user stats
        current_user.analyses_this_month += 1
        current_user.total_analyses += 1
        
        db.commit()
        db.refresh(analysis)
        
        return analysis
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/compare", response_model=ComparisonResponse)
async def compare_scripts(
    request: ScriptCompareRequest,
    current_user: User = Depends(require_plan("pro")),
    db: Session = Depends(get_db)
):
    """
    A/B test two script versions (Pro feature)
    """
    try:
        # Compare scripts
        result = await ScriptAnalyzer.compare_scripts(
            script_a=request.script_a,
            script_b=request.script_b
        )
        
        # Save comparison
        comparison = Comparison(
            user_id=current_user.id,
            winner=result["winner"],
            confidence=result["confidence"],
            reason=result["reason"],
            score_a=result["score_a"],
            score_b=result["score_b"],
            key_differences=result["key_differences"],
            recommendation=result["recommendation"]
        )
        
        db.add(comparison)
        db.commit()
        
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )


@router.post("/improve", response_model=ImprovementResponse)
async def improve_script(
    request: ImproveScriptRequest,
    current_user: User = Depends(require_plan("pro")),
    db: Session = Depends(get_db)
):
    """
    Generate improved version of script (Pro feature)
    """
    try:
        result = await ScriptAnalyzer.generate_improvements(
            script=request.script,
            focus_area=request.focus_area
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Improvement generation failed: {str(e)}"
        )


@router.get("/history", response_model=AnalysisHistory)
async def get_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's analysis history
    """
    # Get total count
    total = db.query(Analysis).filter(Analysis.user_id == current_user.id).count()
    
    # Get analyses
    analyses = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).order_by(
        desc(Analysis.created_at)
    ).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "analyses": analyses
    }


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific analysis by ID
    """
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return analysis


@router.delete("/analysis/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an analysis
    """
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    db.delete(analysis)
    db.commit()
    
    return {"message": "Analysis deleted successfully"}


@router.get("/stats", response_model=UserStats)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user statistics
    """
    # Calculate average score
    avg_score = db.query(func.avg(Analysis.overall_score)).filter(
        Analysis.user_id == current_user.id
    ).scalar() or 0.0
    
    # Get best score
    best_score = db.query(func.max(Analysis.overall_score)).filter(
        Analysis.user_id == current_user.id
    ).scalar() or 0.0
    
    # Get plan limit
    plan_limits = {"free": 3, "pro": 50, "creator": 500}
    plan_limit = plan_limits.get(current_user.plan, 3)
    
    return {
        "total_analyses": current_user.total_analyses,
        "average_score": round(avg_score, 1),
        "best_score": round(best_score, 1),
        "analyses_this_month": current_user.analyses_this_month,
        "plan_limit": plan_limit,
        "remaining_analyses": max(0, plan_limit - current_user.analyses_this_month)
    }
