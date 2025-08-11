import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from collections import defaultdict
import redis

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.redis_client = None
        self.active_sessions = {}
        
        # QI (Quality Indicators) metrics based on 911 standards
        self.qi_metrics = {
            'response_time': {
                'weight': 0.15,
                'target': 10.0,  # seconds to answer
                'description': 'Time to answer emergency call'
            },
            'information_gathering': {
                'weight': 0.25,
                'target': 0.9,  # 90% of required info collected
                'description': 'Completeness of information gathered'
            },
            'caller_control': {
                'weight': 0.20,
                'target': 0.85,  # 85% control maintained
                'description': 'Maintaining control of the call'
            },
            'instructions_given': {
                'weight': 0.20,
                'target': 0.9,  # 90% appropriate instructions
                'description': 'Quality of instructions provided'
            },
            'communication_clarity': {
                'weight': 0.20,
                'target': 0.9,  # 90% clear communication
                'description': 'Clarity of communication'
            }
        }
        
        # Required information by emergency type
        self.required_info = {
            'medical': [
                'location', 'patient_age', 'consciousness_level', 'breathing_status',
                'chief_complaint', 'medical_history'
            ],
            'fire': [
                'location', 'fire_size', 'occupants_inside', 'entry_access',
                'hazards_present', 'smoke_visibility'
            ],
            'police': [
                'location', 'incident_type', 'suspect_description', 'weapons_involved',
                'victim_status', 'suspect_location'
            ]
        }
    
    def initialize(self, redis_url: str):
        """Initialize analytics service"""
        try:
            self.redis_client = redis.from_url(redis_url)
            logger.info("Analytics service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize analytics service: {e}")
            raise
    
    def start_session_analytics(self, session_id: str, scenario_type: str) -> Dict[str, Any]:
        """Start analytics tracking for a session"""
        session_analytics = {
            'session_id': session_id,
            'scenario_type': scenario_type,
            'start_time': datetime.utcnow(),
            'metrics': {
                'response_time': None,
                'information_gathered': [],
                'questions_asked': 0,
                'instructions_given': 0,
                'interruptions': 0,
                'dead_air_time': 0,
                'caller_emotional_progression': [],
                'communication_errors': 0
            },
            'scores': {},
            'events': []
        }
        
        self.active_sessions[session_id] = session_analytics
        
        # Store in Redis
        self.redis_client.setex(
            f"analytics:{session_id}",
            3600,
            json.dumps(session_analytics, default=str)
        )
        
        return session_analytics
    
    def update_session_metrics(self, session_id: str, event_data: Dict[str, Any]):
        """Update metrics for a session based on events"""
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not found in analytics")
                return
            
            session = self.active_sessions[session_id]
            event_type = event_data.get('event_type', '')
            payload = event_data.get('payload', {})
            
            # Update metrics based on event type
            if event_type == 'audio.transcribed':
                self._process_transcript_event(session, payload)
            elif event_type == 'nlp.entities_extracted':
                self._process_entities_event(session, payload)
            elif event_type == 'llm.response_generated':
                self._process_llm_response_event(session, payload)
            elif event_type == 'caller.emotion_changed':
                self._process_emotion_event(session, payload)
            
            # Add event to timeline
            session['events'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'data': payload
            })
            
            # Update Redis
            self.redis_client.setex(
                f"analytics:{session_id}",
                3600,
                json.dumps(session, default=str)
            )
            
        except Exception as e:
            logger.error(f"Error updating session metrics: {e}")
    
    def _process_transcript_event(self, session: Dict, payload: Dict):
        """Process transcript events for analytics"""
        text = payload.get('text', '').lower()
        
        # Count questions asked by dispatcher
        question_indicators = ['what', 'where', 'when', 'how', 'who', 'which', 'why']
        if any(indicator in text for indicator in question_indicators) and text.endswith('?'):
            session['metrics']['questions_asked'] += 1
        
        # Count instructions given
        instruction_indicators = ['please', 'stay', 'remain', 'go', 'move', 'call', 'tell']
        if any(indicator in text for indicator in instruction_indicators):
            session['metrics']['instructions_given'] += 1
        
        # Detect communication issues
        unclear_phrases = ['repeat', 'say again', 'unclear', 'understand', 'what did you say']
        if any(phrase in text for phrase in unclear_phrases):
            session['metrics']['communication_errors'] += 1
    
    def _process_entities_event(self, session: Dict, payload: Dict):
        """Process entity extraction events"""
        entities = payload.get('entities', {})
        scenario_type = session['scenario_type']
        
        # Track information gathering progress
        required_info = self.required_info.get(scenario_type, [])
        
        for entity_type, entity_list in entities.items():
            if entity_list:  # If entities were found
                # Map entity types to required information
                info_mapping = {
                    'locations': 'location',
                    'persons': 'patient_age',
                    'medical_conditions': 'chief_complaint',
                    'weapons': 'weapons_involved'
                }
                
                mapped_info = info_mapping.get(entity_type)
                if mapped_info and mapped_info in required_info:
                    if mapped_info not in session['metrics']['information_gathered']:
                        session['metrics']['information_gathered'].append(mapped_info)
    
    def _process_llm_response_event(self, session: Dict, payload: Dict):
        """Process LLM response events"""
        emotional_state = payload.get('emotional_state', 'CALM')
        intensity = payload.get('intensity', 5)
        
        # Track emotional progression
        session['metrics']['caller_emotional_progression'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'state': emotional_state,
            'intensity': intensity
        })
    
    def _process_emotion_event(self, session: Dict, payload: Dict):
        """Process emotion change events"""
        # This would track emotional state changes
        pass
    
    def calculate_real_time_score(self, session_id: str) -> Dict[str, Any]:
        """Calculate real-time performance score"""
        try:
            if session_id not in self.active_sessions:
                return {'error': 'Session not found'}
            
            session = self.active_sessions[session_id]
            metrics = session['metrics']
            scenario_type = session['scenario_type']
            
            # Calculate individual metric scores
            scores = {}
            
            # Response Time Score (if available)
            if metrics['response_time']:
                target_time = self.qi_metrics['response_time']['target']
                scores['response_time'] = max(0, 1 - (metrics['response_time'] - target_time) / target_time)
            else:
                scores['response_time'] = 1.0  # Assume good if not measured
            
            # Information Gathering Score
            required_info = self.required_info.get(scenario_type, [])
            if required_info:
                info_score = len(metrics['information_gathered']) / len(required_info)
                scores['information_gathering'] = min(1.0, info_score)
            else:
                scores['information_gathering'] = 0.8  # Default score
            
            # Caller Control Score (based on questions asked vs time elapsed)
            elapsed_minutes = (datetime.utcnow() - session['start_time']).total_seconds() / 60
            expected_questions = max(1, elapsed_minutes * 2)  # 2 questions per minute expected
            control_score = min(1.0, metrics['questions_asked'] / expected_questions)
            scores['caller_control'] = control_score
            
            # Instructions Given Score
            expected_instructions = max(1, elapsed_minutes)  # 1 instruction per minute
            instruction_score = min(1.0, metrics['instructions_given'] / expected_instructions)
            scores['instructions_given'] = instruction_score
            
            # Communication Clarity Score
            total_interactions = metrics['questions_asked'] + metrics['instructions_given']
            if total_interactions > 0:
                clarity_score = 1.0 - (metrics['communication_errors'] / total_interactions)
                scores['communication_clarity'] = max(0, clarity_score)
            else:
                scores['communication_clarity'] = 1.0
            
            # Calculate weighted overall score
            overall_score = 0
            for metric, score in scores.items():
                weight = self.qi_metrics[metric]['weight']
                overall_score += score * weight
            
            # Update session scores
            session['scores'] = scores
            session['overall_score'] = overall_score
            
            return {
                'session_id': session_id,
                'overall_score': round(overall_score * 100, 1),  # Convert to percentage
                'individual_scores': {k: round(v * 100, 1) for k, v in scores.items()},
                'metrics_summary': {
                    'questions_asked': metrics['questions_asked'],
                    'information_gathered': len(metrics['information_gathered']),
                    'instructions_given': metrics['instructions_given'],
                    'communication_errors': metrics['communication_errors']
                },
                'calculated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating real-time score: {e}")
            return {'error': str(e)}
    
    def generate_session_report(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive session report"""
        try:
            if session_id not in self.active_sessions:
                return {'error': 'Session not found'}
            
            session = self.active_sessions[session_id]
            final_scores = self.calculate_real_time_score(session_id)
            
            # Calculate additional analytics
            duration = (datetime.utcnow() - session['start_time']).total_seconds()
            
            # Emotional progression analysis
            emotional_states = session['metrics']['caller_emotional_progression']
            emotional_analysis = self._analyze_emotional_progression(emotional_states)
            
            # Performance insights
            insights = self._generate_performance_insights(session, final_scores)
            
            report = {
                'session_summary': {
                    'session_id': session_id,
                    'scenario_type': session['scenario_type'],
                    'duration': round(duration, 1),
                    'overall_score': final_scores.get('overall_score', 0),
                    'completed_at': datetime.utcnow().isoformat()
                },
                'performance_scores': final_scores.get('individual_scores', {}),
                'detailed_metrics': session['metrics'],
                'emotional_analysis': emotional_analysis,
                'performance_insights': insights,
                'recommendations': self._generate_recommendations(session, final_scores)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating session report: {e}")
            return {'error': str(e)}
    
    def _analyze_emotional_progression(self, emotional_states: List[Dict]) -> Dict[str, Any]:
        """Analyze caller's emotional progression"""
        if not emotional_states:
            return {'error': 'No emotional data available'}
        
        states = [state['state'] for state in emotional_states]
        intensities = [state['intensity'] for state in emotional_states]
        
        # Calculate progression metrics
        initial_state = states[0] if states else 'UNKNOWN'
        final_state = states[-1] if states else 'UNKNOWN'
        avg_intensity = np.mean(intensities) if intensities else 0
        intensity_trend = 'stable'
        
        if len(intensities) > 1:
            if intensities[-1] < intensities[0]:
                intensity_trend = 'decreasing'
            elif intensities[-1] > intensities[0]:
                intensity_trend = 'increasing'
        
        return {
            'initial_emotional_state': initial_state,
            'final_emotional_state': final_state,
            'average_intensity': round(avg_intensity, 1),
            'intensity_trend': intensity_trend,
            'state_changes': len(set(states)),
            'progression_timeline': emotional_states
        }
    
    def _generate_performance_insights(self, session: Dict, scores: Dict) -> List[str]:
        """Generate performance insights"""
        insights = []
        metrics = session['metrics']
        individual_scores = scores.get('individual_scores', {})
        
        # Information gathering insights
        if individual_scores.get('information_gathering', 0) < 70:
            insights.append("Focus on gathering more complete information from the caller")
        
        # Communication clarity insights
        if individual_scores.get('communication_clarity', 0) < 80:
            insights.append("Work on clearer communication - reduce need for repetition")
        
        # Caller control insights
        if individual_scores.get('caller_control', 0) < 75:
            insights.append("Ask more directed questions to maintain control of the call")
        
        # Question frequency insight
        duration_minutes = len(session['events']) / 10  # Rough estimate
        if duration_minutes > 0:
            questions_per_minute = metrics['questions_asked'] / duration_minutes
            if questions_per_minute < 1.5:
                insights.append("Increase questioning frequency to gather information more efficiently")
        
        return insights
    
    def _generate_recommendations(self, session: Dict, scores: Dict) -> List[str]:
        """Generate training recommendations"""
        recommendations = []
        individual_scores = scores.get('individual_scores', {})
        
        # Specific recommendations based on weak areas
        weak_areas = [area for area, score in individual_scores.items() if score < 75]
        
        for area in weak_areas:
            if area == 'information_gathering':
                recommendations.append("Practice systematic information gathering protocols")
            elif area == 'communication_clarity':
                recommendations.append("Review clear communication techniques")
            elif area == 'caller_control':
                recommendations.append("Study call control and de-escalation methods")
            elif area == 'instructions_given':
                recommendations.append("Practice providing clear, actionable instructions")
        
        if not recommendations:
            recommendations.append("Continue practicing to maintain high performance standards")
        
        return recommendations
    
    def get_aggregate_analytics(self, timeframe_hours: int = 24) -> Dict[str, Any]:
        """Get aggregate analytics for multiple sessions"""
        try:
            # In production, this would query the database
            # For now, return sample aggregate data
            
            return {
                'timeframe_hours': timeframe_hours,
                'total_sessions': 15,
                'average_score': 82.3,
                'score_distribution': {
                    '90-100': 3,
                    '80-89': 7,
                    '70-79': 4,
                    '60-69': 1,
                    'below_60': 0
                },
                'common_improvement_areas': [
                    'Information Gathering',
                    'Caller Control',
                    'Communication Clarity'
                ],
                'scenario_performance': {
                    'medical': 85.2,
                    'fire': 78.9,
                    'police': 80.1
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting aggregate analytics: {e}")
            return {'error': str(e)}

# Global service instance
analytics_service = AnalyticsService()
