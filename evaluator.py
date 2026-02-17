"""
Player Evaluator Module
Handles dual-value analysis: league scoring value vs. peripheral performance indicators.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PlayerValue:
    """Data class to hold player value metrics."""
    player_name: str
    position: str
    fantasy_score: float
    peripheral_score: float
    value_rating: str  # 'Overperforming', 'Underperforming', 'Aligned', 'Unknown'
    confidence: float  # 0-1 confidence in the rating
    flags: List[str]  # Notable indicators
    

class PlayerEvaluator:
    """
    Evaluates players based on dual-value analysis:
    1. League Scoring Value (The Results)
    2. Performance Peripherals (The Process)
    """
    
    def __init__(self):
        """Initialize the evaluator with league-specific weights."""
        
        # League scoring weights (adjust these based on your league settings)
        self.batter_scoring_weights = {
            'R': 1.0,
            'RBI': 1.0,
            'OBP': 100.0,  # Scaled up since OBP is 0-1
            'SBN2': 2.0,   # More valuable due to CS penalty
            'XBS': 1.5     # Extra base hits plus sac hits
        }
        
        self.pitcher_scoring_weights = {
            'K': 1.0,
            'ERA': -20.0,   # Negative weight, lower is better
            'WHIP': -15.0,  # Negative weight, lower is better
            'RPC': 3.0,     # Relief contribution
            'SPC': 3.0      # Starting contribution
        }
        
        # Peripheral importance weights (for process evaluation)
        self.batter_peripheral_weights = {
            'OPS': 1.0,
            'SLG': 0.8,
            'K%': -0.5,    # Lower is better
            'BB%': 0.5,    # Higher is better
            'Hard_Hit%': 1.2,  # Statcast metric
            'Barrel%': 1.5     # Statcast metric
        }
        
        self.pitcher_peripheral_weights = {
            'K%': 1.5,
            'BB%': -1.0,   # Lower is better
            'K/BB': 1.2,
            'SwStr%': 1.0,  # Swinging strike %
            'Hard_Hit%': -1.0,  # Lower is better for pitchers
            'xFIP': -10.0   # Expected FIP
        }
    
    # ==================== BATTER EVALUATION ====================
    
    def evaluate_batter(self, player_stats: pd.Series, league_avg: Optional[pd.Series] = None) -> PlayerValue:
        """
        Evaluate a batter's dual value.
        
        Args:
            player_stats: Series with player statistics
            league_avg: Optional series with league averages for comparison
            
        Returns:
            PlayerValue object with comprehensive evaluation
        """
        player_name = player_stats.get('Name', player_stats.get('PLAYERNAME', 'Unknown'))
        position = player_stats.get('POS', 'Unknown')
        
        # Calculate fantasy scoring value
        fantasy_score = self._calculate_batter_fantasy_score(player_stats)
        
        # Calculate peripheral score (process metrics)
        peripheral_score = self._calculate_batter_peripheral_score(player_stats, league_avg)
        
        # Determine value rating and confidence
        value_rating, confidence, flags = self._analyze_batter_value_gap(
            player_stats, fantasy_score, peripheral_score, league_avg
        )
        
        return PlayerValue(
            player_name=player_name,
            position=position,
            fantasy_score=fantasy_score,
            peripheral_score=peripheral_score,
            value_rating=value_rating,
            confidence=confidence,
            flags=flags
        )
    
    def _calculate_batter_fantasy_score(self, stats: pd.Series) -> float:
        """Calculate fantasy value based on league scoring categories."""
        score = 0.0
        
        for stat, weight in self.batter_scoring_weights.items():
            value = stats.get(stat, 0)
            if pd.notna(value):
                score += value * weight
        
        return round(score, 2)
    
    def _calculate_batter_peripheral_score(self, stats: pd.Series, league_avg: Optional[pd.Series] = None) -> float:
        """Calculate process quality score based on peripheral metrics."""
        score = 0.0
        stat_count = 0
        
        for stat, weight in self.batter_peripheral_weights.items():
            value = stats.get(stat)
            if pd.notna(value):
                # Normalize against league average if provided
                if league_avg is not None and stat in league_avg:
                    avg_value = league_avg.get(stat, value)
                    if avg_value != 0:
                        normalized_value = (value - avg_value) / avg_value
                        score += normalized_value * weight
                else:
                    # Use raw value scaled appropriately
                    if stat in ['OPS', 'SLG']:
                        score += (value - 0.700) * weight * 10  # Scale OPS/SLG
                    elif stat in ['K%', 'BB%', 'Hard_Hit%', 'Barrel%']:
                        score += value * weight
                    else:
                        score += value * weight
                stat_count += 1
        
        # Average the score if we have multiple stats
        if stat_count > 0:
            score = score / stat_count
        
        return round(score, 2)
    
    def _analyze_batter_value_gap(
        self, 
        stats: pd.Series, 
        fantasy_score: float, 
        peripheral_score: float,
        league_avg: Optional[pd.Series] = None
    ) -> Tuple[str, float, List[str]]:
        """
        Analyze the gap between fantasy performance and peripherals.
        
        Returns:
            Tuple of (value_rating, confidence, flags)
        """
        flags = []
        
        # Normalize scores for comparison
        fantasy_norm = fantasy_score / 100 if fantasy_score != 0 else 0
        peripheral_norm = peripheral_score
        
        # Calculate the gap
        gap = fantasy_norm - peripheral_norm
        
        # Check for specific indicators
        ops = stats.get('OPS', 0)
        obp = stats.get('OBP', 0)
        slg = stats.get('SLG', 0)
        sb = stats.get('SB', 0)
        cs = stats.get('CS', 0)
        xbs = stats.get('XBS', 0)
        
        # Flag analysis
        if ops > 0.850:
            flags.append("Elite OPS")
        elif ops < 0.650:
            flags.append("Low OPS")
        
        if sb > 20 and cs is not None and cs < sb * 0.25:
            flags.append("Elite Base Stealer")
        elif cs is not None and cs > sb * 0.5:
            flags.append("CS Risk")
        
        if xbs is not None and xbs > 50:
            flags.append("Power Hitter")
        
        # Hard Hit % if available (Statcast)
        hard_hit = stats.get('Hard_Hit%')
        if pd.notna(hard_hit):
            if hard_hit > 45:
                flags.append("High Hard Hit%")
            elif hard_hit < 30:
                flags.append("Low Hard Hit%")
        
        # Barrel % if available (Statcast)
        barrel = stats.get('Barrel%')
        if pd.notna(barrel):
            if barrel > 10:
                flags.append("High Barrel%")
        
        # Determine value rating
        confidence = 0.5  # Base confidence
        
        if abs(gap) < 0.3:
            value_rating = "Aligned"
            confidence = 0.85
        elif gap > 0.5:
            value_rating = "Overperforming"
            confidence = 0.75
            flags.append("⚠️ Fantasy > Peripherals")
        elif gap < -0.5:
            value_rating = "Underperforming"
            confidence = 0.75
            flags.append("💎 Peripherals > Fantasy")
        elif gap > 0:
            value_rating = "Slight Overperformance"
            confidence = 0.65
        else:
            value_rating = "Slight Underperformance"
            confidence = 0.65
        
        # Adjust confidence based on sample size
        pa = stats.get('PA', 0)
        if pa is not None:
            if pa < 100:
                confidence *= 0.7
            elif pa > 400:
                confidence *= 1.1
        
        confidence = min(confidence, 1.0)
        
        return value_rating, round(confidence, 2), flags
    
    # ==================== PITCHER EVALUATION ====================
    
    def evaluate_pitcher(self, player_stats: pd.Series, league_avg: Optional[pd.Series] = None) -> PlayerValue:
        """
        Evaluate a pitcher's dual value.
        
        Args:
            player_stats: Series with pitcher statistics
            league_avg: Optional series with league averages for comparison
            
        Returns:
            PlayerValue object with comprehensive evaluation
        """
        player_name = player_stats.get('Name', player_stats.get('PLAYERNAME', 'Unknown'))
        position = player_stats.get('POS', 'P')
        
        # Calculate fantasy scoring value
        fantasy_score = self._calculate_pitcher_fantasy_score(player_stats)
        
        # Calculate peripheral score
        peripheral_score = self._calculate_pitcher_peripheral_score(player_stats, league_avg)
        
        # Determine value rating and confidence
        value_rating, confidence, flags = self._analyze_pitcher_value_gap(
            player_stats, fantasy_score, peripheral_score, league_avg
        )
        
        return PlayerValue(
            player_name=player_name,
            position=position,
            fantasy_score=fantasy_score,
            peripheral_score=peripheral_score,
            value_rating=value_rating,
            confidence=confidence,
            flags=flags
        )
    
    def _calculate_pitcher_fantasy_score(self, stats: pd.Series) -> float:
        """Calculate fantasy value based on league pitching categories."""
        score = 0.0
        
        # Strikeouts (positive)
        k = stats.get('K', stats.get('SO', 0))
        score += k * self.pitcher_scoring_weights['K']
        
        # ERA (negative, lower is better)
        era = stats.get('ERA', 4.5)
        if pd.notna(era):
            # Penalize high ERA, reward low ERA
            score += (3.5 - era) * abs(self.pitcher_scoring_weights['ERA'])
        
        # WHIP (negative, lower is better)
        whip = stats.get('WHIP', 1.3)
        if pd.notna(whip):
            # Penalize high WHIP, reward low WHIP
            score += (1.2 - whip) * abs(self.pitcher_scoring_weights['WHIP'])
        
        # Relief and Starting Contributions
        rpc = stats.get('RPC', 0)
        spc = stats.get('SPC', 0)
        score += rpc * self.pitcher_scoring_weights['RPC']
        score += spc * self.pitcher_scoring_weights['SPC']
        
        return round(score, 2)
    
    def _calculate_pitcher_peripheral_score(self, stats: pd.Series, league_avg: Optional[pd.Series] = None) -> float:
        """Calculate process quality score for pitchers."""
        score = 0.0
        stat_count = 0
        
        for stat, weight in self.pitcher_peripheral_weights.items():
            value = stats.get(stat)
            if pd.notna(value):
                if league_avg is not None and stat in league_avg:
                    avg_value = league_avg.get(stat, value)
                    if avg_value != 0:
                        normalized_value = (value - avg_value) / avg_value
                        score += normalized_value * weight
                else:
                    # Use stat-specific scaling
                    if stat == 'K/BB':
                        score += (value - 2.5) * weight
                    elif stat in ['K%', 'BB%', 'SwStr%', 'Hard_Hit%']:
                        score += value * weight
                    elif stat == 'xFIP':
                        score += (4.0 - value) * abs(weight)
                    else:
                        score += value * weight
                stat_count += 1
        
        if stat_count > 0:
            score = score / stat_count
        
        return round(score, 2)
    
    def _analyze_pitcher_value_gap(
        self,
        stats: pd.Series,
        fantasy_score: float,
        peripheral_score: float,
        league_avg: Optional[pd.Series] = None
    ) -> Tuple[str, float, List[str]]:
        """Analyze pitcher value gap between fantasy and peripherals."""
        flags = []
        
        # Normalize scores
        fantasy_norm = fantasy_score / 100 if fantasy_score != 0 else 0
        peripheral_norm = peripheral_score
        
        gap = fantasy_norm - peripheral_norm
        
        # Extract key stats
        k_pct = stats.get('K%')
        bb_pct = stats.get('BB%')
        k_bb = stats.get('K/BB')
        era = stats.get('ERA')
        whip = stats.get('WHIP')
        ip = stats.get('IP', 0)
        saves = stats.get('SV', 0)
        
        # Flag analysis
        if pd.notna(k_pct):
            if k_pct > 27:
                flags.append("Elite K%")
            elif k_pct < 18:
                flags.append("Low K%")
        
        if pd.notna(bb_pct):
            if bb_pct < 6:
                flags.append("Elite Control")
            elif bb_pct > 10:
                flags.append("Control Issues")
        
        if pd.notna(k_bb):
            if k_bb > 4.0:
                flags.append("Excellent K/BB")
            elif k_bb < 2.0:
                flags.append("Poor K/BB")
        
        if pd.notna(era) and pd.notna(whip):
            # Check for ERA/WHIP mismatch (luck indicator)
            expected_era = (whip - 0.8) * 3 + 2.5  # Rough approximation
            if era < expected_era - 0.5:
                flags.append("⚠️ ERA may regress")
            elif era > expected_era + 0.5:
                flags.append("💎 ERA may improve")
        
        if saves > 20:
            flags.append("Closer")
        
        # xFIP if available
        xfip = stats.get('xFIP')
        if pd.notna(xfip) and pd.notna(era):
            if era < xfip - 0.5:
                flags.append("⚠️ ERA outperforming xFIP")
            elif era > xfip + 0.5:
                flags.append("💎 ERA underperforming xFIP")
        
        # Determine value rating
        confidence = 0.5
        
        if abs(gap) < 0.3:
            value_rating = "Aligned"
            confidence = 0.85
        elif gap > 0.5:
            value_rating = "Overperforming"
            confidence = 0.75
            flags.append("⚠️ Fantasy > Peripherals")
        elif gap < -0.5:
            value_rating = "Underperforming"
            confidence = 0.75
            flags.append("💎 Peripherals > Fantasy")
        elif gap > 0:
            value_rating = "Slight Overperformance"
            confidence = 0.65
        else:
            value_rating = "Slight Underperformance"
            confidence = 0.65
        
        # Adjust confidence by sample size
        if ip < 30:
            confidence *= 0.7
        elif ip > 100:
            confidence *= 1.1
        
        confidence = min(confidence, 1.0)
        
        return value_rating, round(confidence, 2), flags
    
    # ==================== BATCH EVALUATION ====================
    
    def evaluate_roster(self, roster_df: pd.DataFrame, player_type: str = 'batter') -> pd.DataFrame:
        """
        Evaluate an entire roster.
        
        Args:
            roster_df: DataFrame with player statistics
            player_type: 'batter' or 'pitcher'
            
        Returns:
            DataFrame with added evaluation columns
        """
        evaluations = []
        
        for idx, player in roster_df.iterrows():
            if player_type == 'batter':
                eval_result = self.evaluate_batter(player)
            else:
                eval_result = self.evaluate_pitcher(player)
            
            evaluations.append({
                'Player': eval_result.player_name,
                'Position': eval_result.position,
                'Fantasy_Score': eval_result.fantasy_score,
                'Peripheral_Score': eval_result.peripheral_score,
                'Value_Rating': eval_result.value_rating,
                'Confidence': eval_result.confidence,
                'Flags': ', '.join(eval_result.flags)
            })
        
        eval_df = pd.DataFrame(evaluations)
        return eval_df
    
    def identify_buy_low_candidates(self, players_df: pd.DataFrame, player_type: str = 'batter', min_confidence: float = 0.7) -> pd.DataFrame:
        """
        Identify underperforming players who are buy-low candidates.
        
        Args:
            players_df: DataFrame with player statistics
            player_type: 'batter' or 'pitcher'
            min_confidence: Minimum confidence threshold
            
        Returns:
            DataFrame of buy-low candidates
        """
        eval_df = self.evaluate_roster(players_df, player_type)
        
        # Filter for underperforming players with high confidence
        buy_low = eval_df[
            (eval_df['Value_Rating'].str.contains('Underperform')) &
            (eval_df['Confidence'] >= min_confidence)
        ].sort_values('Peripheral_Score', ascending=False)
        
        return buy_low
    
    def identify_sell_high_candidates(self, players_df: pd.DataFrame, player_type: str = 'batter', min_confidence: float = 0.7) -> pd.DataFrame:
        """
        Identify overperforming players who are sell-high candidates.
        
        Args:
            players_df: DataFrame with player statistics
            player_type: 'batter' or 'pitcher'
            min_confidence: Minimum confidence threshold
            
        Returns:
            DataFrame of sell-high candidates
        """
        eval_df = self.evaluate_roster(players_df, player_type)
        
        # Filter for overperforming players
        sell_high = eval_df[
            (eval_df['Value_Rating'].str.contains('Overperform')) &
            (eval_df['Confidence'] >= min_confidence)
        ].sort_values('Fantasy_Score', ascending=False)
        
        return sell_high


# ==================== UTILITY FUNCTIONS ====================

def compare_players(player1_stats: pd.Series, player2_stats: pd.Series, player_type: str = 'batter') -> Dict:
    """
    Compare two players side by side.
    
    Args:
        player1_stats: First player's statistics
        player2_stats: Second player's statistics
        player_type: 'batter' or 'pitcher'
        
    Returns:
        Dictionary with comparison results
    """
    evaluator = PlayerEvaluator()
    
    if player_type == 'batter':
        eval1 = evaluator.evaluate_batter(player1_stats)
        eval2 = evaluator.evaluate_batter(player2_stats)
    else:
        eval1 = evaluator.evaluate_pitcher(player1_stats)
        eval2 = evaluator.evaluate_pitcher(player2_stats)
    
    return {
        'player1': eval1,
        'player2': eval2,
        'fantasy_advantage': eval1.player_name if eval1.fantasy_score > eval2.fantasy_score else eval2.player_name,
        'peripheral_advantage': eval1.player_name if eval1.peripheral_score > eval2.peripheral_score else eval2.player_name,
        'recommended': eval1.player_name if (eval1.fantasy_score + eval1.peripheral_score) > (eval2.fantasy_score + eval2.peripheral_score) else eval2.player_name
    }
